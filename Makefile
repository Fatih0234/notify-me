list-x:
	@gh api repos/Fatih0234/x-botty/contents/config.json --jq '.content' \
		| base64 -d | python3 -c "import sys,json; [print('@'+a) for a in json.load(sys.stdin).get('accounts',[])]"

list-youtube:
	@gh api repos/Fatih0234/youtube-competitor-tracker/contents/config.json --jq '.content' \
		| base64 -d | python3 -c "import sys,json; [print(c) for c in json.load(sys.stdin).get('channels',[])]"
