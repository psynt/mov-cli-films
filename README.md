<div align="center">

  # mov-cli-anitaku
  <sub>A mov-cli v4 plugin for watching anitaku.</sub>

  <img src="https://github.com/mov-cli/mov-cli-gogotaku/assets/132799819/1436339c-f2c3-4c37-b9ae-0da6b83faf8d">

</div>

> [!Warning]
> Currently work in progress.

## Installation
Here's how to install and add the plugin to mov-cli.

1. Install the pip package.
```sh
pip install git+https://github.com/mov-cli/mov-cli-anitaku 
```
2. Then add the plugin to your mov-cli config.
```sh
mov-cli -e
```
```toml
[mov-cli.plugins]
anitaku = "mov-cli-anitaku"
```

## Usage
```sh
mov-cli lycoris recoil --scraper anitaku
```
