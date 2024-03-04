<div align="center">

  # mov-cli-vadapav
  <sub>A mov-cli v4 plugin for watching Vadapav.</sub>

  <img src="https://github.com/mov-cli/mov-cli-vadapav/assets/132799819/6406133d-f840-424b-a1c9-04599fadb0a7">


</div>

> [!Warning]
> Currently work in progress.

## Installation
Here's how to install and add the plugin to mov-cli.

1. Install the pip package.
```sh
pip install git+https://github.com/mov-cli/mov-cli-vadapav 
```
2. Then add the plugin to your mov-cli config.
```sh
mov-cli -e
```
```toml
[mov-cli.plugins]
vadapav = "mov-cli-vadapav"
```

## Usage
```sh
mov-cli the rookie --scraper vadapav
```
