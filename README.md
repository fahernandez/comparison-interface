[![pipeline status](https://gitlab.bham.ac.uk/seymourg-bsbt/comparison-interface/badges/main/pipeline.svg)](https://gitlab.bham.ac.uk/seymourg-bsbt/comparison-interface/-/commits/main)

[![coverage report](https://gitlab.bham.ac.uk/seymourg-bsbt/comparison-interface/badges/main/coverage.svg)](https://gitlab.bham.ac.uk/seymourg-bsbt/comparison-interface/-/commits/main)

[![Latest Release](https://gitlab.bham.ac.uk/seymourg-bsbt/comparison-interface/-/badges/release.svg)](https://gitlab.bham.ac.uk/seymourg-bsbt/comparison-interface/-/releases)

# Comparison Interface
This repository provides a web interface to facilitate the collection of comparative judgement. In only a couple of minutes, it lets you deploy a web interface to collect comparative judgement by simply requiring items images (i.e. to be compared) as input. The results can be exported to an excel file which can then be directly processed using the BSBT package to obtain a ranking. There is not restriction on the item's nature but the software has been used previously  on geospatial datasets to be processed with the Bayesian Spatial Bradley--Terry model BSBT - https://github.com/rowlandseymour/BSBT).

## Terms
* ***judge***: Person who makes the comparison between items.
* ***groups***: Item's natural clustering.

## Software main characteristics.
1. The entire text of the website can be changed from a single configuration point.
2. Custom weights can be defined for the items pairs.
3. Multiple items group can be defined to respond for judges acuate knowledge.
3. Instructions can be written/formatted in Google docs and then render in the website keeping the original look and feel. (This is an optional section)
4. Ethics agreement can be written/formatted in Google docs and then render in the website keeping the original look and feel. (This is an optional section)
5. Ethics agreement can be configured to be mandatory before making the item's comparison. (This is an optional feature)
6. Custom fields can be configured to be required when the judge is registering on the website.
7. The entire database can be dump to an excel file.


## Quick Set-up
This sequence of commands will allow you visualize one of the pre-configured examples.

### Prerequisites
1. You are using a Linux or Mac computer.
2. python > 3.8.0 is already installed in your computer.

### Set-up Steps
1. Open a terminal console an run these commands.
```bash
pip3 install -r requirements.txt
flask --app website --debug setup example/config-equal-item-weights.json
flask --app website --debug run --host=0.0.0.0 --port=5001
```
2. Navigate in you preferred navigation browser to http://127.0.0.1:5001
3. (optional) Try a different configuration example.
```bash
flask --app website --debug reset example/config-custom-item-weights.json
flask --app website --debug run --host=0.0.0.0 --port=5002
```
4. (optional) Navigate in you preferred navigation browser to http://127.0.0.1:5002
5. (optional) Export the information to an excel file.
```bash
flask --app website --debug export
```
6. (optional) The information is exported on instance/export.xls


## Custom Set-up
Follow the next step to make a custom configuration of the project.

### Requirements
1. The images of the items being compared.
    * These images must be at least 300x300 pixels.
    * The name of the images cannot be repeated.
    * Valid images format accepted: png, jpg or jpeg,
2. Create a custom configuration file.
    * Refer to ***example/config-equal-item-weights.json*** to configure a scenario when the weight of the items being compared at the same.
    * Refer to ***example/config-custom-item-weights.json*** to configure a scenario when the weight of the items being compared at the same.

### Steps
1. Delete the content of the folder ***static/image*** and copy inside your images.
2. Copy your configuration file to the folder ***example/***.
3. Open a terminal console an run these commands.
```bash
pip3 install -r requirements.txt
flask --app website --debug setup example/{the_name_of_your_configuration_file}.json
flask --app website --debug run --host=0.0.0.0 --port=5001
```
4. (optional) Export the information to an excel file.
```bash
flask --app website --debug export
```
5. (optional) The information is exported on ***instance/export.xls***

### Troubleshooting
1. The configuration file requires an specific format. Try to follow one of the examples supplied with this project to avoid unexpected problems.
2. When running the ***setup*** command, the software validates the format of the configuration file. These messages will guide you on the issues being introduced.

## Support
For support, send an email to [fabian.hnz@gmail.com](mailto:fabian.hnz@gmail.com). I try to review the email everyday.

## Contributing
We welcome any contribution to the project. Please refer to .gitlab-ci.yml for details on the project's linter and test standards.

## Authors and acknowledgment
* Bertrand Perrat, The University of Nottingham: V1 main project contributor.
* Fabián Hernández, The University of Nottingham: V2 main project contributor.
* Rowland Seymour, The university of birmingham: Project's director.

## License
<!--- https://gist.github.com/lukas-h/2a5d00690736b4c3a7ba -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


