import os

import buildbot
import buildbot.process.factory
from buildbot.steps.source import SVN, Git
from buildbot.steps.shell import Configure, ShellCommand
from buildbot.process.properties import WithProperties

def getPollyBuildFactory():
    llvm_srcdir = "llvm.src"
    llvm_objdir = "llvm.obj"
    cloog_srcdir = "cloog.src"
    cloog_installdir = "cloog.install"

    f = buildbot.process.factory.BuildFactory()

    # Determine the build directory.
    f.addStep(buildbot.steps.shell.SetProperty(name="get_builddir",
                                               command=["pwd"],
                                               property="builddir",
                                               description="set build dir",
                                               workdir="."))

    # Checkout sources.
    # Get Cloog and isl
    f.addStep(Git(repourl='git://repo.or.cz/cloog.git',
                  mode='update',
                  workdir=cloog_srcdir))
    f.addStep(ShellCommand(name="get_isl",
                               command=["./get_submodules.sh"],
                               haltOnFailure=True,
                               description=["get isl submodule"],
                               workdir=cloog_srcdir))
    # Get LLVM and Polly
    f.addStep(SVN(name='svn-llvm',
                  mode='update',
                  baseURL='http://llvm.org/svn/llvm-project/llvm/',
                  defaultBranch='trunk',
                  workdir=llvm_srcdir))
    f.addStep(SVN(name='svn-polly',
                  mode='update',
                  baseURL='http://llvm.org/svn/llvm-project/polly/',
                  defaultBranch='trunk',
                  workdir='%s/tools/polly' % llvm_srcdir))
    # Build Cloog and isl
    f.addStep(ShellCommand(name="autogen-cloog-isl",
                               command=["./autogen.sh"],
                               haltOnFailure=True,
                               description=["autogen cloog and isl"],
                               workdir=cloog_srcdir))
    confargs = []
    confargs.append(WithProperties("%%(builddir)s/%s/configure"
                                    % cloog_srcdir))
    confargs.append(WithProperties("--prefix=%%(builddir)s/%s"
                                    % cloog_installdir))
    f.addStep(Configure(name="cloog-configure",
                        command=confargs,
                        workdir=cloog_srcdir,
                        description=['cloog-configure']))
    f.addStep(ShellCommand(name="build-cloog-isl",
                               command=["make"],
                               haltOnFailure=True,
                               description=["build cloog and isl"],
                               workdir=cloog_srcdir))
    f.addStep(ShellCommand(name="install-cloog-isl",
                               command=["make", "install"],
                               haltOnFailure=True,
                               description=["install cloog and isl"],
                               workdir=cloog_srcdir))
    # Create configuration files with cmake
    f.addStep(ShellCommand(name="create-build-dir",
                               command=["mkdir", llvm_objdir],
                               haltOnFailure=False,
                               description=["create build dir"],
                               workdir="."))
    f.addStep(ShellCommand(name="cmake-configure",
                               command=["cmake", "../%s" %llvm_srcdir],
                               haltOnFailure=False,
                               description=["cmake configure"],
                               workdir=llvm_objdir))
    cloogpath = WithProperties("-DCMAKE_PREFIX_PATH=%%(builddir)s/%s"
                                % cloog_installdir)
    f.addStep(ShellCommand(name="cmake-cloog-path",
                               command=["cmake", cloogpath, "."],
                               haltOnFailure=True,
                               description=["cmake cloog path"],
                               workdir=llvm_objdir))
    # Build Polly
    f.addStep(ShellCommand(name="build_polly",
                               command=["make"],
                               haltOnFailure=True,
                               description=["build polly"],
                               workdir=llvm_objdir))
    # Test Polly
    f.addStep(ShellCommand(name="test_polly",
                               command=["make", "polly-test"],
                               haltOnFailure=True,
                               description=["test polly"],
                               workdir=llvm_objdir))
    return f
