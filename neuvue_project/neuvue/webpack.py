from webpack_loader.loader import WebpackLoader
import json


class MultipleWebpackLoader(WebpackLoader):
    def load_assets(self):
        complete_stats = {"status": None, "assets": {}, "chunks": {}}

        for fn in self.config["STATS_FILES"]:
            with open(fn) as fp:
                stats = json.load(fp)
                if stats["status"] != "done":
                    raise ValueError(f"Failed to load webpack status: {fn}")
                complete_stats["assets"] = {
                    **complete_stats["assets"],
                    **stats["assets"],
                }
                complete_stats["chunks"] = {
                    **complete_stats["chunks"],
                    **stats["chunks"],
                }
        complete_stats["status"] = "done"
        return complete_stats
