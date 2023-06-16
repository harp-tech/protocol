import sys
import markdown as md
import pandas as pd
import yaml
#tabulate

def main(argv):
	path_to_whoami = argv[0]

	yml = yaml.load(open(path_to_whoami), yaml.Loader)

	devices = yml["devices"]
	d = pd.DataFrame.from_dict(devices, orient='index')
	d.index.names = ['WhoAmI']
	d = d.fillna('')
	d.to_markdown("DeviceWhoAmI.md")

if __name__ == "__main__":
	main(sys.argv[1:])

