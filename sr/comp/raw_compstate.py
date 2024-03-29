"""Utilities for working with raw Compstate repositories."""

import os
import subprocess
import yaml

from .comp import SRComp


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

    # Load and save related functionality

    def load(self):
        """Load the state as an ``SRComp`` instance."""
        return SRComp(self._path)

    def load_shepherds(self):
        """Load the shepherds' state."""

        layout = self.layout['teams']
        layout_map = {r['name']: r for r in layout}
        shepherds = self.shepherding['shepherds']

        for s in shepherds:
            regions = s['regions']
            teams = []
            for region_name in regions:
                region = layout_map[region_name]
                teams += region['teams']
            s['teams'] = teams

            assert len(teams) == len(set(teams)), "Some teams listed in more than one region!"

        return shepherds

    def get_score_path(self, match):
        """Get the absolute path to the score file for the given match."""
        filename = "{0:0>3}.yaml".format(match.num)
        relpath = os.path.join(match.type.value, match.arena, filename)
        return os.path.realpath(os.path.join(self._path, relpath))

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

    @property
    def deployments(self):
        deployments_name = 'deployments.yaml'
        deployments_path = os.path.join(self._path, deployments_name)

        with open(deployments_path, 'r') as dp:
            raw_deployments = yaml.load(dp)

        hosts = raw_deployments['deployments']
        return hosts

    @property
    def shepherding(self):
        """Provides access to the raw shepherding data.
           Most consumers actually want to use ``load_shepherds`` instead."""
        path = os.path.join(self._path, 'shepherding.yaml')

        with open(path) as shepherding_file:
            return yaml.load(shepherding_file)

    @property
    def layout(self):
        path = os.path.join(self._path, 'layout.yaml')

        with open(path) as layout_file:
            return yaml.load(layout_file)

    # Git repo related functionality

    def git(self, command_pieces, err_msg=None, return_output=False):
        command = ['git'] + list(command_pieces)

        if return_output:
            stderr = subprocess.STDOUT
            def func(*args, **kwargs):
                return subprocess.check_output(*args, **kwargs).decode("utf-8")
        else:
            func = subprocess.check_call
            stderr = None

        try:
            return func(command, cwd=self._path, stderr=stderr)
        except subprocess.CalledProcessError as e:
            if err_msg:
                if e.output:
                    err_msg += '\n\n' + e.output

                raise RuntimeError(err_msg)
            else:
                raise
        except OSError:
            if err_msg:
                raise RuntimeError(err_msg)
            else:
                raise

    @property
    def has_changes(self):
        """
        Whether or not there are any changes to files in the state,
        including untracked files.
        """
        output = self.git(["status", "--porcelain"], return_output=True)
        return len(output) != 0

    def show_changes(self):
        self.git(['status'])

    def show_remotes(self):
        self.git(['remote', '-v'])

    def push(self, where, revspec, err_msg=None, force=False):
        args = ["push", where, revspec]
        if force:
            args.insert(1, '--force')
        self.git(args, err_msg)

    def rev_parse(self, revision):
        output = self.git(["rev-parse", '--verify', revision], return_output=True,
                          err_msg="Unknown revision '{0}'.".format(revision))
        return output.strip()

    def has_commit(self, commit):
        """Whether or not the given commit is known to this repository."""
        try:
            self.rev_parse(commit + "^{commit}")
            return True
        except RuntimeError:
            return False

    def _is_parent(self, parent, child):
        try:
            revspec = "{0}..{1}".format(parent, child)
            revs = self.git(['rev-list', '-n1', revspec, '--'],
                            return_output=True)
            # rev-list prints the revisions which are parents of 'child',
            # up to and including 'parent'; any output therefore tells us
            # that they're related
            return len(revs.strip()) != 0
        except subprocess.CalledProcessError:
            # One or both revisions are unknown
            return False

    def has_ancestor(self, commit):
        return self._is_parent(commit, 'HEAD')

    def has_descendant(self, commit):
        return self._is_parent('HEAD', commit)

    def reset_hard(self):
        self.git(["reset", "--hard", "HEAD"], err_msg="Git reset failed.")

    def reset_and_fast_forward(self):
        self.reset_hard()

        self.pull_fast_forward()

    def pull_fast_forward(self):
        if self._local_only:
            return

        self.git(["pull", "--ff-only", "origin", "master"],
                 err_msg="Git pull failed, deal with the merge manually.")

    def stage(self, file_path):
        """
        Stage the given file.

        :param str file_path: A path to the file to stage. This should
                              either be an absolute path, or one relative
                              to the compstate.
        """
        self.git(["add", file_path])

    def fetch(self, where='origin', quiet=False):
        self.git(['fetch', where], return_output=quiet)

    def checkout(self, what):
        self.git(['checkout', what])

    def commit(self, commit_msg, allow_empty=False):
        args = ["commit", "-m", commit_msg]
        if allow_empty:
            args += ['--allow-empty']
        self.git(args, return_output=True, err_msg="Git commit failed.")

    def commit_and_push(self, commit_msg, allow_empty=False):
        self.commit(commit_msg, allow_empty)

        if self._local_only:
            return

        self.push("origin", "master",
                  err_msg="Git push failed, deal with the merge manually.")
