from pathlib import Path

path = Path("chernarus/traders/index.html")
text = path.read_text(encoding="utf-8")
old = '''{"slug":"attachment-trader","name":"Attachment Trader","title":"Weapon Attachments Trader","location":"Scorched Isle Market","region":"Mainland Chernarus","currency":"","specialty":"Attachments • Weapon Attachments • Optics • Magazines • Info Coming Soon","summary":"Attachment trader information is coming soon.","buys":[],"sells":[],"group":"Scorched Isle Market","order":45,"comingSoon":true},'''
new = '''{"slug":"attachment-trader","name":"Attachment Trader","title":"Weapon Attachments Trader","location":"Scorched Isle Market","region":"Mainland Chernarus","currency":"USD","specialty":"Attachments • Optics • Magazines • Ammunition • My DF • Bayonets • Stocks • Handguards","summary":"Scorched Isle Market's weapon attachment specialist, buying and selling attachments, optics, magazines and ammunition with live server pricing. Select 40mm grenades are sell-to-trader only.","buys":["Weapon attachments","Optics","Magazines","Ammunition","My DF attachments","My DF magazines","My DF ammunition","Harald's ammunition","Morty's ammunition","Bayonets","Buttstocks","Handguards","40mm grenades"],"sells":["Weapon attachments","Optics","Magazines","Ammunition","My DF attachments","My DF magazines","My DF ammunition","Harald's ammunition","Morty's ammunition","Bayonets","Buttstocks","Handguards","Weapon cleaning kits"],"image":"assets/traders/attachment-trader.svg","group":"Scorched Isle Market","order":45},'''

if old in text:
    path.write_text(text.replace(old, new), encoding="utf-8")
    print("Activated attachment trader directory card.")
elif new in text:
    print("Attachment trader directory card is already active.")
else:
    raise SystemExit("Attachment trader placeholder was not found; refusing to edit an unexpected directory layout.")
