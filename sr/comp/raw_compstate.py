"""Utilities for working with raw Compstate repositories."""

import os
import subprocess
import yaml

from sr.comp.comp import SRComp


class RawCompstate(object):
    """
    Helper class to interact with a Compstate as raw files in a Git repository
    on disk.

    :param str path: The path to the Compstate repository.
    :param bool local_only: If true, this disabled the pulling, commiting and
                            pushing functionality.
    """

    def __init__(self, path, local_only):
        self._path = path
        self._local_only = local_only

    ## Load and save related functionality

    def load(self):
        """Load the state as an ``SRComp`` instance."""
        return SRComp(self._path)


    def get_score_path(self, match):
        """Get the absolute path to the score file for the given match."""
        filename = "{0:0>3}.yaml".format(match.num)
        return os.path.join(self._path, match.type.value, match.arena, filename)


    def load_score(self, match):
        """Load raw score data for the given match."""
        path = self.get_score_path(match)
        # Scores are basic data only
        with open(path) as fd:
            return yaml.safe_load(fd)


    def save_score(self, match, score):
        """Save raw score data for the given match."""
        path = self.get_score_path(match)

        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(path, "w") as fd:
            yaml.safe_dump(score, fd, default_flow_style=False)


    # Git repo related functionality

    def git(self, command_pieces, err_msg=None):
        command = ['git'] + list(command_pieces)
        try:
            subprocess.check_call(command, cwd=self._path)
        except (OSError, subprocess.CalledProcessError):
            if err_msg:
                raise RuntimeError(err_msg)
            else:
                raise


    def reset_hard(self):
        self.git(["reset", "--hard", "HEAD"], err_msg="Git reset failed.")


    def reset_and_fast_forward(self):
        self.reset_hard()

        if self._local_only:
            return

        self.git(["pull", "--ff-only", "origin", "master"],
                 err_msg="Git pull failed, deal with the merge manually.")


    def stage(self, file_path):
        self.git(["add", os.path.realpath(file_path)])


    def commit(self, commit_msg):
        self.git(["commit", "-m", commit_msg], err_msg="Git commit failed.")


    def commit_and_push(self, commit_msg):
        self.commit(commit_msg)

        if self._local_only:
            return

        self.git(["push", "origin", "master"],
                 err_msg="Git push failed, deal with the merge manually.")
