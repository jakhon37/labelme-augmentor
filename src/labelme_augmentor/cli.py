"""Command-line interface for labelme-augmentor."""

import argparse
import logging

from .config import load_config
from .core import DatasetProcessor


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='LabelMe Augmentation Tool with configurable per-class augmentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use config file
  labelme-augment --config config/labelme_augmentation_config.yaml
  
  # Override specific paths
  labelme-augment --config config/labelme_augmentation_config.yaml \\
      --input /path/to/input --output /path/to/output
  
  # Clear checkpoint and reprocess all
  labelme-augment --config config/labelme_augmentation_config.yaml --clear-checkpoint
  
  # Single-threaded for debugging
  labelme-augment --config config/labelme_augmentation_config.yaml --workers 1
        """,
    )

    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to YAML configuration file',
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Override input JSON directory',
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Override output directory',
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of worker processes (overrides config)',
    )
    parser.add_argument(
        '--clear-checkpoint',
        action='store_true',
        help='Clear checkpoint and reprocess all files',
    )
    parser.add_argument(
        '--no-checkpoint',
        action='store_true',
        help='Disable checkpoint/resume functionality',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging',
    )

    args = parser.parse_args()

    # Load configuration (with validation disabled by default for backward compatibility)
    config = load_config(args.config, validate=False)

    # Override with command-line arguments
    if args.input:
        config.setdefault('paths', {})['input_json_dir'] = args.input
    if args.output:
        config.setdefault('paths', {})['output_dir'] = args.output
    if args.workers is not None:
        config.setdefault('general', {})['num_workers'] = args.workers
    if args.no_checkpoint:
        config.setdefault('general', {})['resume_from_checkpoint'] = False
    if args.debug:
        config.setdefault('general', {})['log_level'] = 'DEBUG'

    # Initialize processor
    processor = DatasetProcessor(config)

    # Clear checkpoint if requested
    if args.clear_checkpoint:
        logging.info("Clearing checkpoint...")
        processor.checkpoint_manager.clear()

    # Process dataset
    processor.process_dataset()


if __name__ == "__main__":
    main()
