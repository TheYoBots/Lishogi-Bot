import yaml
import os
import os.path
import logging

logger = logging.getLogger(__name__)


def load_config(config_file):
    with open(config_file) as stream:
        try:
            CONFIG = yaml.safe_load(stream)
        except Exception as e:
            logger.error("There appears to be a syntax problem with your config.yml")
            raise e
            
        if "LISHOGI_BOT_TOKEN" in os.environ:
            CONFIG["token"] = os.environ["LISHOGI_BOT_TOKEN"]

        # [section, type, error message]
        sections = [["token", str, "Section `token` must be a string wrapped in quotes."],
                    ["url", str, "Section `url` must be a string wrapped in quotes."],
                    ["engine", dict, "Section `engine` must be a dictionary with indented keys followed by colons.."],
                    ["challenge", dict, "Section `challenge` must be a dictionary with indented keys followed by colons.."]]
        for section in sections:
            if section[0] not in CONFIG:
                raise Exception("Your config.yml does not have required section `{}`.".format(section[0]))
            elif not isinstance(CONFIG[section[0]], section[1]):
                raise Exception(section[2])

        engine_sections = [["dir", str, "´dir´ must be a string wrapped in quotes."],
                           ["name", str, "´name´ must be a string wrapped in quotes."]]
        for subsection in engine_sections:
            if subsection[0] not in CONFIG["engine"]:
                raise Exception("Your config.yml does not have required `engine` subsection `{}`.".format(subsection))
            if not isinstance(CONFIG["engine"][subsection[0]], subsection[1]):
                raise Exception("´engine´ subsection {}".format(subsection[2]))

        if CONFIG["token"] == "xxxxxxxxxxxxxxxx":
            raise Exception("Your config.yml has the default Lishogi API token. This is probably wrong.")

        if not os.path.isdir(CONFIG["engine"]["dir"]):
            raise Exception("Your engine directory `{}` is not a directory.".format(CONFIG["engine"]["dir"]))

        engine = os.path.join(CONFIG["engine"]["dir"], CONFIG["engine"]["name"])

        if not os.path.isfile(engine) and CONFIG["engine"]["protocol"] != "homemade":
            raise Exception("The engine %s file does not exist." % engine)

        if not os.access(engine, os.X_OK) and CONFIG["engine"]["protocol"] != "homemade":
            raise Exception("The engine %s doesn't have execute (x) permission. Try: chmod +x %s" % (engine, engine))

    return CONFIG
