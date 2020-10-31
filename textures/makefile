empty-arena.png: arena.svg
	inkscape --export-png=$@ $< --export-width=2048 --export-height=2048
	# Remove the Alpha channel which Inkscape *always* includes, even if the
	# background is a fixed colour.
	convert $@ -alpha deactivate $@
