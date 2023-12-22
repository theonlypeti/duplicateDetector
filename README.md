# Duplicate Detector

Duplicate Detector is a Python application that scans a specified directory for duplicate image and video files.

It uses the `imageio` library to read files and compare them after matching file sizes and file dimensions.

## Requirements

You can install the packages using pip:

```bash
pip install -r requirements.txt
```

## Usage

You can run the application with various command line arguments:

- `--path`: Path to the folder to scan.
- `--date`: Date and time (yyyy.mm.dd hh:mm), where files only added after this are checked for duplicates.
- `--debug`: Enable debug mode.
- `--logfile`: Turns on logging to a text file.
- `--remove`: Prompts the user to delete the duplicates. Use this option with caution, as it will permanently delete files.
- `--no_video`: Skips videos.
- `--profiling`: Measures the runtime and outputs it to profile.prof.

Example usage:

```bash
python main.py --path /path/to/scan --date "2024.01.01 00:00" --remove
```

## Contributing
This project was a programming exercise to learn multiprocessing, os functions and reading of image files. This was not meant to be a serious project but contributions to Duplicate Detector are welcome. Please open an issue or submit a pull request on GitHub.  
## License

Duplicate Detector is open source software released under the [MIT license](https://opensource.org/licenses/MIT).