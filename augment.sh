

# CONFIG_FILE=/home/aoi-linux/workspace/defecTRAIN/DATA/AUGMENT/AUGMENT_CODE/configs/labelme_augmentation_configINKblack.yaml
CONFIG_FILE=/home/aoi-linux/workspace/defecTRAIN/DATA/AUGMENT/AUGMENT_CODE/configs/test_config.yaml

labelme-augment --config $CONFIG_FILE

# Example command to run the script with a specific config file
# bash augment.sh --config /path/to/your/labelme_augmentation_config.yaml

echo "Augmentation process completed."
