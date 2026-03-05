"""Dataset processor with multiprocessing and checkpoint support."""

import json
import logging
import os
from functools import partial
from glob import glob
from multiprocessing import Pool, cpu_count
from typing import Dict, List

from tqdm import tqdm

from ..utils import CheckpointManager, setup_logging_from_config
from .augmentor import Augmentor


class DatasetProcessor:
    """
    Main processor with multiprocessing and checkpoint support.
    """

    def __init__(self, config: Dict) -> None:
        """Initialize the dataset processor with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Paths
        paths = config.get('paths', {})
        self.input_json_dir = paths.get('input_json_dir')
        self.output_dir = paths.get('output_dir')

        if not self.input_json_dir or not self.output_dir:
            raise ValueError("input_json_dir and output_dir must be specified in config")

        # Setup logging before anything else
        setup_logging_from_config(config, self.output_dir)

        # Output structure
        output_config = config.get('output', {})
        self.output_images_dir = os.path.join(
            self.output_dir, output_config.get('images_subdir', 'images')
        )
        self.output_json_dir = os.path.join(
            self.output_dir, output_config.get('annotations_subdir', 'annotations')
        )
        self.debug_dir = os.path.join(self.output_dir, output_config.get('debug_subdir', 'debug'))
        self.create_debug = output_config.get('create_debug_visualizations', True)

        for d in [self.output_images_dir, self.output_json_dir]:
            os.makedirs(d, exist_ok=True)

        if self.create_debug:
            os.makedirs(self.debug_dir, exist_ok=True)

        # Get JSON files
        self.json_files = sorted(glob(os.path.join(self.input_json_dir, "*.json")))

        if not self.json_files:
            raise ValueError(f"No JSON files found in {self.input_json_dir}")

        logging.info(f"Found {len(self.json_files)} LabelMe JSON files to process.")

        # Checkpoint manager
        general_config = config.get('general', {})
        checkpoint_file = general_config.get('checkpoint_file', 'augmentation_checkpoint.json')
        checkpoint_path = os.path.join(self.output_dir, checkpoint_file)
        self.checkpoint_manager = CheckpointManager(checkpoint_path)
        self.use_checkpoint = general_config.get('resume_from_checkpoint', True)

        # Multiprocessing
        num_workers = general_config.get('num_workers')
        if num_workers is None:
            self.num_workers = max(1, cpu_count() - 1)
        else:
            self.num_workers = max(1, num_workers)

        logging.info(f"Using {self.num_workers} worker(s) for processing")

    def collect_class_names(self) -> List[str]:
        """Collect all unique class names from all JSON files.
        
        Returns:
            Sorted list of unique class names
        """
        all_class_names = set()

        for json_path in self.json_files:
            with open(json_path, 'r') as f:
                data = json.load(f)

            for shape in data.get('shapes', []):
                all_class_names.add(shape['label'])

        class_names = sorted(list(all_class_names))
        logging.info(f"Found {len(class_names)} classes: {class_names}")

        return class_names

    def process_dataset(self) -> None:
        """Process entire dataset with augmentations using multiprocessing."""
        # Collect class names
        class_names = self.collect_class_names()

        # Initialize augmentor
        augmentor = Augmentor(class_names, self.config)

        # Filter files based on checkpoint
        files_to_process = []
        for json_path in self.json_files:
            if self.use_checkpoint and self.checkpoint_manager.is_processed(json_path):
                logging.debug(f"Skipping {json_path} (already processed)")
                continue
            files_to_process.append(json_path)

        if not files_to_process:
            logging.info(
                "All files already processed. Use resume_from_checkpoint: false to reprocess."
            )
            return

        logging.info(
            f"Processing {len(files_to_process)} files "
            f"({len(self.json_files) - len(files_to_process)} skipped from checkpoint)"
        )

        # Process files
        total_saved = 0

        if self.num_workers == 1:
            # Single-threaded processing
            for json_path in tqdm(files_to_process, desc="Processing files", unit="file"):
                result = self._process_single_file(json_path, augmentor)
                total_saved += result['num_saved']

                if result['success']:
                    self.checkpoint_manager.mark_processed(json_path)
                    self.checkpoint_manager.save_checkpoint()
        else:
            # Multi-threaded processing
            process_func = partial(
                self._process_single_file_static,
                output_images_dir=self.output_images_dir,
                output_json_dir=self.output_json_dir,
                debug_dir=self.debug_dir,
                create_debug=self.create_debug,
                class_names=class_names,
                config=self.config,
            )

            with Pool(processes=self.num_workers) as pool:
                results = list(
                    tqdm(
                        pool.imap(process_func, files_to_process),
                        total=len(files_to_process),
                        desc="Processing files",
                        unit="file",
                    )
                )

            for json_path, result in zip(files_to_process, results):
                total_saved += result['num_saved']
                if result['success']:
                    self.checkpoint_manager.mark_processed(json_path)

            # Save checkpoint after batch
            self.checkpoint_manager.save_checkpoint()

        # Print summary
        self.print_summary(class_names, total_saved)

    def _process_single_file(self, json_path: str, augmentor: Augmentor) -> Dict:
        """Process a single file (instance method).
        
        Args:
            json_path: Path to JSON file
            augmentor: Augmentor instance
            
        Returns:
            Dictionary with processing results
        """
        case_id = os.path.splitext(os.path.basename(json_path))[0]

        try:
            num_saved = augmentor.process_file(
                json_path,
                self.output_images_dir,
                self.output_json_dir,
                self.debug_dir,
                self.create_debug,
            )
            logging.info(f"✓ {case_id}: Generated {num_saved} files")
            return {'success': True, 'num_saved': num_saved, 'case_id': case_id}

        except Exception as e:
            logging.error(f"✗ {case_id}: Error - {e}")
            return {'success': False, 'num_saved': 0, 'case_id': case_id, 'error': str(e)}

    @staticmethod
    def _process_single_file_static(
        json_path: str,
        output_images_dir: str,
        output_json_dir: str,
        debug_dir: str,
        create_debug: bool,
        class_names: List[str],
        config: Dict,
    ) -> Dict:
        """Process a single file (static method for multiprocessing).
        
        Args:
            json_path: Path to JSON file
            output_images_dir: Output directory for images
            output_json_dir: Output directory for JSON files
            debug_dir: Output directory for debug visualizations
            create_debug: Whether to create debug visualizations
            class_names: List of class names
            config: Configuration dictionary
            
        Returns:
            Dictionary with processing results
        """
        # Create augmentor in worker process
        augmentor = Augmentor(class_names, config)
        case_id = os.path.splitext(os.path.basename(json_path))[0]

        try:
            num_saved = augmentor.process_file(
                json_path, output_images_dir, output_json_dir, debug_dir, create_debug
            )
            return {'success': True, 'num_saved': num_saved, 'case_id': case_id}

        except Exception as e:
            logging.error(f"✗ {case_id}: Error - {e}")
            return {'success': False, 'num_saved': 0, 'case_id': case_id, 'error': str(e)}

    def print_summary(self, class_names: List[str], total_saved: int) -> None:
        """Print processing summary.
        
        Args:
            class_names: List of class names
            total_saved: Total number of files saved
        """
        print("\n" + "=" * 70)
        print("AUGMENTATION COMPLETE!")
        print("=" * 70)
        print(f"Input directory: {self.input_json_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"\nDirectories created:")
        print(f"  • Images: {self.output_images_dir}")
        print(f"  • Annotations: {self.output_json_dir}")
        if self.create_debug:
            print(f"  • Debug visualizations: {self.debug_dir}")
        print(f"\nClasses processed ({len(class_names)}):")
        for i, cls in enumerate(class_names, 1):
            print(f"  {i}. {cls}")
        print(f"\nTotal files generated: {total_saved}")
        print(f"Checkpoint saved to: {self.checkpoint_manager.checkpoint_file}")
        print("=" * 70)
