# Logging Configuration Guide

## Overview

The package now supports flexible logging with:
- ✅ File logging (detailed logs saved to output directory)
- ✅ Console logging (less verbose, configurable)
- ✅ Separate log levels for file and console
- ✅ Automatic log file naming with timestamps
- ✅ Full configuration control via YAML

## Quick Start

### Default Behavior
By default, logs are:
- **File**: INFO level, saved to `output_dir/augmentation_YYYYMMDD_HHMMSS.log`
- **Console**: WARNING level (only warnings and errors shown)

### Configuration Options

Add a `logging` section to your config:

```yaml
general:
  log_level: INFO  # File logging level

logging:
  log_to_file: true          # Save logs to file
  log_to_console: true       # Show logs in console
  console_level: WARNING     # Console logging level
  log_filename: null         # Auto-generate filename
```

## Log Levels

Choose from (most to least verbose):
- **DEBUG**: Everything (very detailed)
- **INFO**: General information (default for file)
- **WARNING**: Warnings and errors (default for console)
- **ERROR**: Errors only
- **CRITICAL**: Critical errors only

## Common Configurations

### 1. Quiet Console, Detailed File (Recommended)
```yaml
general:
  log_level: INFO

logging:
  log_to_file: true
  log_to_console: true
  console_level: WARNING  # Only show warnings/errors in console
```

**Result:**
- Console: Clean, only shows important messages
- File: Detailed logs for debugging

### 2. Verbose Mode (Debugging)
```yaml
general:
  log_level: DEBUG

logging:
  log_to_file: true
  log_to_console: true
  console_level: DEBUG  # Show everything in console too
```

**Result:**
- Console: Very verbose
- File: Very verbose

### 3. Quiet Mode (Production)
```yaml
general:
  log_level: WARNING

logging:
  log_to_file: true
  log_to_console: true
  console_level: ERROR  # Only errors in console
```

**Result:**
- Console: Very quiet
- File: Only warnings and errors

### 4. File Only (No Console Output)
```yaml
general:
  log_level: INFO

logging:
  log_to_file: true
  log_to_console: false  # No console output
```

**Result:**
- Console: Only progress bars
- File: Full logs

### 5. Console Only (No File)
```yaml
general:
  log_level: INFO

logging:
  log_to_file: false  # No file output
  log_to_console: true
  console_level: INFO
```

**Result:**
- Console: Full logs
- File: None

## Custom Log Filename

```yaml
logging:
  log_filename: "my_augmentation.log"  # Custom name
```

Or let it auto-generate:
```yaml
logging:
  log_filename: null  # Auto: augmentation_20240127_153045.log
```

## Log File Location

Logs are saved to: `{output_dir}/{log_filename}`

Example:
- Config: `output_dir: "data/output"`
- Log file: `data/output/augmentation_20240127_153045.log`

## Example Output

### Console (WARNING level)
```
📄 Logging to file: data/output/augmentation_20240127_153045.log
WARNING: Mask has no defects after augmentation
ERROR: Failed to load image: file_not_found.jpg
```

### Log File (INFO level)
```
2024-01-27 15:30:45 - labelme_augmentor.core.processor - INFO - Found 10 LabelMe JSON files to process.
2024-01-27 15:30:45 - labelme_augmentor.core.processor - INFO - Using 4 worker(s) for processing
2024-01-27 15:30:46 - labelme_augmentor.core.augmentor - INFO - ✓ image_1: Generated 6 files
2024-01-27 15:30:47 - labelme_augmentor.validation.validator - WARNING - Mask has no defects after augmentation
2024-01-27 15:30:48 - labelme_augmentor.core.augmentor - ERROR - Failed to load image: file_not_found.jpg
```

## Recommended Settings

### For Development
```yaml
general:
  log_level: DEBUG
logging:
  console_level: INFO  # Show progress
```

### For Production
```yaml
general:
  log_level: INFO
logging:
  console_level: WARNING  # Clean console
```

### For Debugging Issues
```yaml
general:
  log_level: DEBUG
logging:
  console_level: DEBUG  # See everything
```

## Benefits

✅ **Clean Console**: No clutter with WARNING level
✅ **Detailed Logs**: Full information in log files
✅ **Easy Debugging**: Check log files when issues occur
✅ **Progress Visibility**: Progress bars always shown
✅ **Flexible**: Configure per your needs

## Example Usage

```bash
# Use config with logging settings
labelme-augment --config configs/examples/logging_example.yaml

# Output:
# 📄 Logging to file: data/output/augmentation_20240127_153045.log
# Processing files: 100%|████████| 10/10 [00:05<00:00]
# ✅ AUGMENTATION COMPLETE!
```

Check the log file for detailed information!
