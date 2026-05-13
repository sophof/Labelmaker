1. Remove height, width and depth options altogether and remove write yaml function. You can only change the text options (font, size and emboss/deboss)

2. Create the colors in such a way that bambustudio can use and map them to my filament. see https://wiki.bambulab.com/en/bambu-studio/Standard-3MF-File-Color-Parsing

3. Propose refactoring of logic so that things are better structured and easier to parse. For instance _label_utils is getting very full and has logic for different things. Writing text, overflow warnings, etc. Propose a new way of ordering things. Also check other folders and code.