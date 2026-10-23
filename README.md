# Beneath the Ashes

Official website for the Beneath the Ashes DayZ community.

## Website
https://beneaththeashesdayz.github.io

## Updating traders
Trader information lives in `traders.json`.

After changing trader information, run:

```bash
python build_traders.py
```

This regenerates the searchable trader directory and every individual trader profile.

## Trader images
Place trader images in `assets/traders/` using the filename listed for that trader in `traders.json`.

Current starter filenames:
- `gabi.jpg`
- `hassan.jpg`
- `kaito.jpg`
- `peter.jpg`
- `keiko.jpg`

Individual trader pages include Open Graph metadata so their permanent URLs can generate rich link previews in Discord.
