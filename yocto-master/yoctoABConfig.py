################################################################################
# Yocto Build Server Developer Configuration
################################################################################
# Elizabeth Flanagan <elizabeth.flanagan@intel.com>
################################################################################
# Copyright (C) 2011-2012 Intel Corp.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import copy, random, os, datetime 
import cPickle as pickle
from time import strftime
from email.Utils import formatdate
from twisted.python import log
from buildbot.changes.pb import PBChangeSource
from buildbot.process import factory
from buildbot.process.properties import WithProperties
from buildbot.process.buildstep import BuildStep, LoggingBuildStep, LoggedRemoteCommand, RemoteShellCommand
from buildbot.scheduler import Triggerable
from buildbot.scheduler import Scheduler
from buildbot.scheduler import Periodic
from buildbot.scheduler import Nightly
from buildbot.schedulers import timed
from buildbot.schedulers import triggerable
from buildbot.steps.trigger import Trigger
from buildbot.steps import blocker
from buildbot.process import buildstep
from buildbot.status.results import SUCCESS, FAILURE
import buildbot.steps.blocker
from buildbot.steps import shell
from buildbot.steps.shell import ShellCommand
from buildbot.steps.source import Git
from buildbot.process.properties import Property
from buildbot.steps.slave import SetPropertiesFromEnv

yocto_projname = "Gumstix CI"
yocto_projurl = "http://buildbot.gumstix.org/"
yocto_sources = []
yocto_sources.append(PBChangeSource())
yocto_sched = []
yocto_builders = []
defaultenv = {}
layerid = 0
releases = ["denzil", "danny"]
ABBASE = os.environ.get("PWD")
SOURCE_DL_DIR = os.environ.get("SOURCE_DL_DIR")
LSB_SSTATE_DIR = os.environ.get("LSB_SSTATE_DIR")
SOURCE_SSTATE_DIR = os.environ.get("SOURCE_SSTATE_DIR")
CLEAN_SOURCE_DIR = os.environ.get("CLEAN_SOURCE_DIR")
PUBLISH_BUILDS = os.environ.get("PUBLISH_BUILDS")
PUBLISH_SOURCE_MIRROR = os.environ.get("PUBLISH_SOURCE_MIRROR")
PUBLISH_SSTATE = os.environ.get("PUBLISH_SSTATE")
BUILD_PUBLISH_DIR = os.environ.get("BUILD_PUBLISH_DIR")
BUILD_HISTORY_COLLECT = os.environ.get("BUILD_HISTORY_COLLECT")
BUILD_HISTORY_DIR = os.environ.get("BUILD_HISTORY_DIR")
BUILD_HISTORY_REPO = os.environ.get("BUILD_HISTORY_REPO")
SSTATE_PUBLISH_DIR = os.environ.get("SSTATE_PUBLISH_DIR")
SOURCE_PUBLISH_DIR = os.environ.get("SOURCE_PUBLISH_DIR")
EMGD_DRIVER_DIR = os.environ.get("EMGD_DRIVER_DIR")
SLAVEBASEDIR = os.environ.get("SLAVEBASEDIR")
ADTREPO_POPULATE = os.environ.get("ADTREPO_POPULATE")
ADTREPO_DEV_POPULATE = os.environ.get("ADTREPO_DEV_POPULATE")
ADTREPO_GENERATE_INSTALLER = os.environ.get("ADTREPO_GENERATE_INSTALLER")
ADTREPO_GENERATE_DEV_INSTALLER = os.environ.get("ADTREPO_GENERATE_DEV_INSTALLER")
ADTREPO_URL = os.environ.get("ADTREPO_URL")
ADTREPO_PATH = os.environ.get("ADTREPO_PATH")
ADTREPO_DEV_URL = os.environ.get("ADTREPO_DEV_URL")
ADTREPO_DEV_PATH = os.environ.get("ADTREPO_DEV_PATH")
if not BUILD_PUBLISH_DIR:
    BUILD_PUBLISH_DIR = "/tmp"
BUILD_HISTORY_COLLECT = os.environ.get("BUILD_HISTORY_COLLECT")
BUILD_HISTORY_REPO = os.environ.get("BUILD_HISTORY_REPO")
PERSISTDB_DIR = os.environ.get("PERSISTDB_DIR")
MAINTAIN_PERSISTDB = os.environ.get("MAINTAIN_PERSISTDB")
 
# Very useful way of grabbing nightly-arch names
nightly_arch = []
nightly_arch.append("x86")
nightly_arch.append("x86-64")
nightly_arch.append("arm")
nightly_arch.append("mips")
nightly_arch.append("ppc")

# Trying to access Properties within a factory can sometimes be problematic.
# This is here for convenience.
defaultenv["ADTDEV"]="False"
defaultenv['LCONF_VERSION'] = "5"
defaultenv['ENABLE_SWABBER'] = ""
defaultenv['WORKDIR'] = ""
defaultenv['FuzzArch'] = ""
defaultenv['FuzzImage'] = ""
defaultenv['FuzzSDK'] = ""
defaultenv['machine'] = ""
defaultenv['DEST'] = ""
defaultenv['BRANCH'] = ""
defaultenv['POKYREPO'] = ""
defaultenv['SDKMACHINE'] = "i686"
defaultenv['DL_DIR'] = SOURCE_DL_DIR
defaultenv['LSB_SSTATE_DIR'] = LSB_SSTATE_DIR
defaultenv['SSTATE_DIR'] = SOURCE_SSTATE_DIR
defaultenv['SSTATE_BRANCH'] = ""
defaultenv['BUILD_HISTORY_COLLECT'] = BUILD_HISTORY_COLLECT
defaultenv['BUILD_HISTORY_DIR'] = BUILD_HISTORY_DIR
defaultenv['BUILD_HISTORY_REPO'] = BUILD_HISTORY_REPO
defaultenv['ADTREPO_POPULATE'] = ADTREPO_POPULATE
defaultenv['ADTREPO_DEV_POPULATE'] = ADTREPO_DEV_POPULATE
defaultenv['ADTREPO_GENERATE_INSTALLER'] = ADTREPO_GENERATE_INSTALLER
defaultenv['ADTREPO_GENERATE_DEV_INSTALLER'] = ADTREPO_GENERATE_DEV_INSTALLER
defaultenv['ADTREPO_URL'] = ADTREPO_URL
defaultenv['ADTREPO_PATH'] = ADTREPO_PATH
defaultenv['ADTREPO_DEV_URL'] = ADTREPO_DEV_URL
defaultenv['ADTREPO_DEV_PATH'] = ADTREPO_DEV_PATH
defaultenv['EMGD_DRIVER_DIR'] = EMGD_DRIVER_DIR
defaultenv['SLAVEBASEDIR'] = SLAVEBASEDIR
defaultenv['PERSISTDB_DIR'] = PERSISTDB_DIR
defaultenv['MAINTAIN_PERSISTDB'] = MAINTAIN_PERSISTDB
defaultenv['ABBASE'] = ABBASE
defaultenv['MIGPL'] = "False"
defaultenv['SSTATE_MIRRORS'] = "file://.* http://sstate-cache.gumstix.org/PATH" 
defaultenv['SOURCE_MIRROR_URL'] = "http://source-cache.gumstix.org" 

class NoOp(buildstep.BuildStep):
    """
    A build step that does nothing except finish with a caller-
    supplied status (default SUCCESS).
    """
    parms = buildstep.BuildStep.parms + ['result']

    result = SUCCESS
    flunkOnFailure = True

    def start(self):
        self.step_status.setText([self.name])
        self.finished(self.result)

class setDest(LoggingBuildStep):
    renderables = [ 'abbase', 'workdir', 'btarget' ]
    
    def __init__(self, abbase=None, workdir=None, btarget=None, **kwargs):
        LoggingBuildStep.__init__(self, **kwargs)
        self.workdir = workdir
        self.abbase = abbase
        self.btarget = btarget
        self.description = ["Setting", "Destination"]
        self.addFactoryArguments(abbase=abbase, workdir=workdir, btarget=btarget)

    def describe(self, done=False):
        return self.description

    def setStepStatus(self, step_status):
        LoggingBuildStep.setStepStatus(self, step_status)

    def setDefaultWorkdir(self, workdir):
        self.workdir = self.workdir or workdir

    def start(self):
        try:
	        self.getProperty('DEST')
        except:
            DEST = os.path.join(BUILD_PUBLISH_DIR.strip('"').strip("'"), self.btarget)
            DEST_DATE=datetime.datetime.now().strftime("%Y%m%d")
            DATA_FILE = os.path.join(self.abbase, self.btarget + "_dest.dat")
            try:
                pfile = open(DATA_FILE, 'rb')
                data = pickle.load(pfile)
            except:
                pfile = open(DATA_FILE, 'wb')
                data = {}
                pickle.dump(data, pfile)
                pfile.close()
            # we can't os.path.exists here as we don't neccessarily have
            # access to the slave dest from master. So we keep a cpickle of 
            # the dests.
            try:
                # if the dictionary entry exists, we increment value by one, then repickle
                REV=data[os.path.join(DEST, DEST_DATE)]
                REV=int(REV) + 1
                #data[os.path.join(DEST, DEST_DATE)]=int(REV)
            except:
                REV=1
            data[os.path.join(DEST, DEST_DATE)] = REV
            pfile = open(DATA_FILE, 'wb')
            pickle.dump(data, pfile)
            pfile.close()
            DEST = os.path.join(DEST, DEST_DATE + "-" + str(REV))
            self.setProperty('DEST', DEST)
	return self.finished(SUCCESS)

class YoctoBlocker(buildbot.steps.blocker.Blocker):

    VALID_IDLE_POLICIES = buildbot.steps.blocker.Blocker.VALID_IDLE_POLICIES + ("run",)

    def _getBuildStatus(self, botmaster, builderName):
        try:
            builder = botmaster.builders[builderName]
        except KeyError:
            raise BadStepError("no builder named %r" % builderName)
        
        myBuildStatus = self.build.getStatus()
        builderStatus = builder.builder_status
        matchingBuild = None

        all_builds = (builderStatus.buildCache.values() +
                      builderStatus.getCurrentBuilds())

        for buildStatus in all_builds:
            if self.buildsMatch(myBuildStatus, buildStatus):
                matchingBuild = buildStatus
                break

        if matchingBuild is None:
            msg = "no matching builds found in builder %r" % builderName
            if self.idlePolicy == "error":
                raise BadStepError(msg + " (is it idle?)")
            elif self.idlePolicy == "ignore":
                self._log(msg + ": skipping it")
                return None
            elif self.idlePolicy == "block":
                self._log(msg + ": will block until it starts a build")
                self._blocking_builders.add(builderStatus)
                return None
            elif self.idlePolicy == "run":
                self._log(msg + ": start build for break the block")
                from buildbot.process.builder import BuilderControl
                from buildbot.sourcestamp import SourceStamp
                bc = BuilderControl(builder, botmaster)
                bc.submitBuildRequest(SourceStamp(),
                                      "start for break the block",
                                      props = {
                                               'uniquebuildnumber': (myBuildStatus.getProperties()['uniquebuildnumber'], 'Build'),
                                              }
                                     )
                all_builds = (builderStatus.buildCache.values() +
                              builderStatus.getCurrentBuilds())

                for buildStatus in all_builds:
                    if self.buildsMatch(myBuildStatus, buildStatus):
                        matchingBuild = buildStatus
                        break
                self._blocking_builders.add(builderStatus)

        self._log("found builder %r: %r", builderName, builder)
        return matchingBuild

    def buildsMatch(self, buildStatus1, buildStatus2):
        return \
        buildStatus1.getProperties().has_key("DEST") and \
        buildStatus2.getProperties().has_key("DEST") and \
        buildStatus1.getProperties()["DEST"] == \
        buildStatus2.getProperties()["DEST"]

def setAllEnv(factory):
    factory.addStep(SetPropertiesFromEnv(variables=["SLAVEBASEDIR"]))
    factory.addStep(SetPropertiesFromEnv(variables=["BUILD_HISTORY_DIR"]))
    factory.addStep(SetPropertiesFromEnv(variables=["BUILD_HISTORY_REPO"]))
    factory.addStep(SetPropertiesFromEnv(variables=["BUILD_HISTORY_COLLECT"]))

def createBBLayersConf(factory, defaultenv, btarget=None, bsplayer=False, provider=None, buildprovider=None):
    factory.addStep(SetPropertiesFromEnv(variables=["SLAVEBASEDIR"]))
    factory.addStep(ShellCommand(doStepIf=getSlaveBaseDir,
                    env=copy.copy(defaultenv),
                    command='echo "Getting the slave basedir"'))
    if defaultenv['MIGPL']=="True":
        slavehome = "meta-intel-gpl"
    else:
        slavehome = defaultenv['ABTARGET']
    BBLAYER = defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/build/conf/bblayers.conf"
    factory.addStep(ShellCommand(description="Ensuring a bblayers.conf exists",
                    command=["sh", "-c", WithProperties("echo '' > %s/" + slavehome + "/build/build/conf/bblayers.conf", 'SLAVEBASEDIR')],
                    timeout=60))
    factory.addStep(ShellCommand(warnOnFailure=True, description="Removing old bblayers.conf",
                    command=["sh", "-c", WithProperties("rm %s/" + slavehome + "/build/build/conf/bblayers.conf", 'SLAVEBASEDIR')],
                    timeout=60))
    factory.addStep(ShellCommand(description="Adding LCONF to bblayers.conf",
                    command=["sh", "-c", WithProperties("echo 'LCONF_VERSION = \"%s\" \n' > %s/" + slavehome + "/build/build/conf/bblayers.conf",    'LCONF_VERSION', 'SLAVEBASEDIR')],
                    timeout=60))
    fout = ""
    fout = fout + 'BBPATH = "${TOPDIR}" \n'
    fout = fout + 'BBFILES ?="" \n'
    fout = fout + 'BBLAYERS += " \ \n'
    if buildprovider=="yocto":
        fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/poky/meta \ \n"
        fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/poky/meta-yocto \ \n"
        if provider=="gumstix":
            fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/poky/meta-openembedded/meta-gnome \ \n"
            fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/poky/meta-openembedded/meta-oe \ \n"
            fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/poky/meta-openembedded/meta-xfce \ \n"
            fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/poky/meta-gumstix \ \n"
    elif buildprovider=="oe":
        fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/meta \ \n"
    if bsplayer==True and provider=="intel":
        if defaultenv['BRANCH'] != "edison":
             fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + '/build/yocto/meta-intel' + ' \ \n'
        fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + '/build/yocto/meta-intel/meta-' + btarget.replace("-noemgd", "") + ' \ \n'
        fout = fout + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + '/build/yocto/meta-intel/meta-tlk \ \n'
    elif bsplayer==True and provider=="fsl" and btarget == "p1022ds":
        fout = fout + defaultenv['SLAVEBASEDIR']  + "/" + slavehome + '/build/yocto/meta-fsl-ppc \ \n'
    fout = fout + ' " \n'
    factory.addStep(ShellCommand(description="Creating bblayers.conf",
                    command="echo '" +  fout + "'>>" + BBLAYER,
                    timeout=60))
    if buildprovider=="yocto" and provider!="gumstix":
        factory.addStep(ShellCommand(doStepIf=checkYoctoBSPLayer, description="Adding meta-yocto-bsp layer to bblayers.conf",
                        command="echo 'BBLAYERS += \"" + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/poky/meta-yocto-bsp\"'>>" + BBLAYER,
                        timeout=60))
    if defaultenv['ABTARGET'] == 'nightly-x32':
        factory.addStep(ShellCommand(doStepIf=lambda(step): step.build.getProperties().has_key("PRE13"), description="Adding meta-x32 layer to bblayers.conf",
                        command="echo 'BBLAYERS += \"" + defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/meta-x32\"'>>" + BBLAYER,
                        timeout=60))

def doMasterTest(step):
    branch = step.getProperty("branch")
    if branch == "master":
        return True
    else:
        return False

def setLCONF(factory, defaultenv):
    if defaultenv['MIGPL']=="True":
        slavehome = "meta-intel-gpl"
    else:
        slavehome = defaultenv['ABTARGET']
    BBLAYER = defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/build/conf/bblayers.conf"
    factory.addStep(shell.SetProperty(
                    command="cat " + BBLAYER + "|grep LCONF |sed 's/LCONF_VERSION = \"//'|sed 's/\"//'",
                    property="LCONF_VERSION")) 
def setSDKVERSION(factory, defaultenv):
    if defaultenv['MIGPL']=="True":
        slavehome = "meta-intel-gpl"
    else:
        slavehome = defaultenv['ABTARGET']
    SDKVERSION = defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/meta-yocto/conf/distro/poky.conf"
    factory.addStep(shell.SetProperty(
                    command="cat " + SDKVERSION + "|grep 'DISTRO_VERSION ='|sed 's/DISTRO_VERSION = //'|sed 's/-${DATE}//'|sed 's/\"//g'",
                    property="SDKVERSION"))

def checkYoctoBSPLayer(step):
    lconf = step.getProperty("LCONF_VERSION")
    if int(lconf) < 5:
        step.setProperty("PRE13", "True")
        return False
    else:
        return True
def checkBranchMaster(step):
    branch = step.getProperty("branch")
    if branch == "master":
        return True 
    else:
        return False 
def checkBranchDev(step):
    branch = step.getProperty("branch")
    if branch == "dev":
        return True
    else:
        return False

def runImage(factory, machine, distro, bsplayer, provider, buildhistory):
    factory.addStep(ShellCommand, description=["cleaning deploy directory"],
		    command=["sh", "-c", WithProperties("rm -rf tmp/deploy/images/")],
		    workdir="build/build",
		    timeout=100)

    factory.addStep(ShellCommand, description=["cleaning configuration directory"],
		    command=["sh", "-c", WithProperties("rm -rf conf")],
		    workdir="build/build",
		    timeout=10)
    factory.addStep(ShellCommand(doStepIf=checkBranchMaster,  description=["setting up build"],
                    command=["yocto-autobuild-preamble"],
                    workdir="build",
                    env=copy.copy(defaultenv),
                    timeout=24400))
    factory.addStep(ShellCommand(doStepIf=checkBranchDev,  description=["setting up build"],
                    command=["yocto-autobuild-preamble-danny"],
                    workdir="build", 
                    env=copy.copy(defaultenv),
                    timeout=24400))

    if distro.startswith("poky"):
        buildprovider="yocto"
    else:
        buildprovider="oe"
    factory.addStep(ShellCommand(doStepIf=getSlaveBaseDir,
                    env=copy.copy(defaultenv),
                    command='echo "Getting the slave basedir"'))
    if defaultenv['MIGPL']=="True":
        slavehome = "meta-intel-gpl"
    else:
        slavehome = defaultenv['ABTARGET']
    BBLAYER = defaultenv['SLAVEBASEDIR'] + "/" + slavehome + "/build/build/conf/bblayers.conf"
    defaultenv['MACHINE'] = machine
    factory.addStep(ShellCommand, description=["Building", machine, "gumstix-console-image"],
                    command=["yocto-autobuild", "gumstix-console-image", "-k", "-D"],
                    env=copy.copy(defaultenv),
                    timeout=24400)
    factory.addStep(ShellCommand, description=["Building", machine, "gumstix-xfce-image"],
                    command=["yocto-autobuild", "gumstix-xfce-image", "-k", "-D"],
                    env=copy.copy(defaultenv),
                    timeout=24400)
    factory.addStep(ShellCommand(description="uploading to S3", 
				 command=["UploadToS3WithMD5.py", "build/tmp/deploy/images/",  WithProperties("%s", "branch")], workdir="build",
 				 timeout=600))

def runImageLinaro(factory):
    factory.addStep(ShellCommand, description=["Getting Overo Config file to build hwpack"],
                    command=["git", "clone", "https://github.com/adam-lee/linaro-overo-config.git"],
                    timeout=60, workdir="build/")
    factory.addStep(ShellCommand, description=["Cleaning old stuff"],
		    command=["rm", "-rf", "new_kernel_build;", "rm", "-rf", "linaro-image-tools"],
                    timeout=600, workdir="build/")
    factory.addStep(ShellCommand, description=["Cloning Linux Kernel"],
 		    command=["git", "clone", "https://github.com/adam-lee/linux-1.git", "-b", "omap-3.5"],
                    timeout=24400)
    factory.addStep(ShellCommand, description=["Cleaning old Ubuntu Kernel CI Tool"],
		    command=["rm", "-rf", "ubuntu-kernel-ci"],
                    timeout=600, workdir="build/")
    factory.addStep(ShellCommand, description=["Checking Out Ubuntu Kernel CI Tool"],
 		    command=["git", "clone", "https://github.com/adam-lee/ubuntu-kernel-ci.git", "-b", "overo"])
    factory.addStep(ShellCommand, description=["building hwpack"], 
		    command=["ubuntu-kernel-ci/scripts/package_kernel", "-k", "867031F1",  "--cfg", "ubuntu-kernel-ci/configs/sakoman-omap-3.5.cfg", "do_test_build_source_pkg=true", "do_lava_testing=true", "job_flavour=omap"])
    factory.addStep(ShellCommand, description=["Upload hwpack"], 
		    command=["UploadLinaroToS3WithMD5.py", "./"],
                    workdir="build/out")

def runSanityTest(factory, machine, image):
    defaultenv['MACHINE'] = machine
    factory.addStep(ShellCommand, description=["Running sanity test for", 
                    machine, image], 
                    command=["yocto-autobuild-sanitytest", image], 
                    env=copy.copy(defaultenv), 
                    timeout=2400)
def getSlaveBaseDir(step):
    defaultenv['SLAVEBASEDIR'] = step.getProperty("SLAVEBASEDIR")
    return True

def getDest(step):
    defaultenv['DEST'] = step.getProperty("DEST")
    return True

def runArchPostamble(factory, distro, target):
        factory.addStep(ShellCommand(doStepIf=doNightlyArchTest,
                        description="Syncing bb_persist_data.sqlite3 to main persistdb area",
                        workdir="build/build/tmp/cache",
                        command=["cp", "-R", "bb_persist_data.sqlite3", WithProperties(defaultenv['PERSISTDB_DIR'] + "/%s/%s/" + distro + "/bb_persist_data.sqlite3", "buildername", "otherbranch")],
                        timeout=2000))

def runPreamble(factory, target):
    factory.addStep(SetPropertiesFromEnv(variables=["SLAVEBASEDIR"]))
    factory.addStep(ShellCommand(doStepIf=getSlaveBaseDir,
                    env=copy.copy(defaultenv),
                    command='echo "Getting the slave basedir"'))
    if defaultenv['MIGPL']=="True":
        slavehome = "meta-intel-gpl"
    else:
        slavehome = defaultenv['ABTARGET']
    factory.addStep(shell.SetProperty(
                    command="uname -a",
                    property="UNAME"))
    factory.addStep(shell.SetProperty(
                    command="echo $HOSTNAME",
                    property="HOSTNAME"))
    factory.addStep(ShellCommand(
                    description=["Building on", WithProperties("%s", "HOSTNAME"),  WithProperties("%s", "UNAME")],
                    command=["echo", WithProperties("%s", "HOSTNAME"),  WithProperties("%s", "UNAME")]))
    factory.addStep(setDest(workdir=WithProperties("%s", "workdir"), btarget=target, abbase=defaultenv['ABBASE']))

def getRepo(step):
    gitrepo = step.getProperty("repository")
    try:
        branch = step.getProperty("branch")
        if gitrepo == "git://git.yoctoproject.org/poky-contrib":
            for release in releases:
                if release in branch:
                    step.setProperty("otherbranch", "denzil")
                    break
                else:
                    step.setProperty("otherbranch", "denzil")
#                    step.setProperty("otherbranch", "master")
            step.setProperty("short-repo-name", "poky-contrib")
        elif gittype == "git://git.yoctoproject.org/poky":
            if branch != "master":
                step.setProperty("otherbranch", "denzil")
                #step.setProperty("otherbranch", branch)
            else:
                #step.setProperty("otherbranch", "master")
                step.setProperty("otherbranch", "denzil")
            #step.setProperty("short-repo-name", "poky")
    except:
        step.setProperty("short-repo-name", "poky")
        step.setProperty("otherbranch", branch)
        pass
    #cgitrepo = gitrepo.replace("git://git.yoctoproject.org/",  "http://git.yoctoproject.org/cgit/cgit.cgi/")
    #step.setProperty("cgitrepo", cgitrepo)
    defaultenv['BRANCH']=step.getProperty("otherbranch")
    return True

def setOECoreRepo(step):
    step.setProperty("repository", "git://git.openembedded.org/openembedded-core")
    step.setProperty("repourl", "git://git.openembedded.org/openembedded-core")
    step.setProperty("branch", "master")
    step.setProperty("short-repo-name", "openembedded-core")
    #step.setProperty("otherbranch", "master")
    step.setProperty("otherbranch", "denzil")
    cgitrepo = ("http://git.openembedded.org/cgit/cgit.cgi/")
    step.setProperty("cgitrepo", cgitrepo)
    defaultenv['BRANCH']=step.getProperty("otherbranch")
    return True

def checkMultiOSSState(step):
    branch = step.getProperty("otherbranch")
    if branch == 'edison' or branch == 'denzil':
        step.setProperty("PRE13", "True")
        return False
    return True
 
def getTag(step):
    try:
        tag = step.getProperty("pokytag")
    except:
        step.setProperty("pokytag", "HEAD")
        pass
    return True

def makeCheckout(factory):
	if defaultenv['ABTARGET'] == "overo":
            factory.addStep(ShellCommand(workdir="./", command=["curl", "-o", "repo", "https://dl-ssl.google.com/dl/googlesource/git-repo/repo"], timeout=1000))
            factory.addStep(ShellCommand(workdir="./", command=["chmod", "a+x", "repo"], timeout=1000))
            factory.addStep(ShellCommand(workdir="./", command=["sudo", "mv", "repo", "/usr/local/bin"], timeout=1000))
	    factory.addStep(ShellCommand(workdir="build", command=["repo", "init", "-u", "https://github.com/gumstix/Gumstix-YoctoProject-Repo.git", "-b", WithProperties("%s", "branch")], timeout=1000))
            factory.addStep(ShellCommand(workdir="build/poky", command=["repo", "sync"], timeout=1000))
def makeTarball(factory):
    factory.addStep(ShellCommand, description="Generating release tarball", 
                    command=["yocto-autobuild-generate-sources-tarball", "nightly", "1.1pre", 
                    WithProperties("%s", "branch")], timeout=120)
    publishArtifacts(factory, "tarball", "build/build/tmp")


def makeLayerTarball(factory):
    factory.addStep(ShellCommand, description="Generating release tarball",
                    command=["yocto-autobuild-generate-sources-tarball", "nightly", "1.1pre",
                    WithProperties("%s", "layer0branch")], timeout=120)
    publishArtifacts(factory, "layer-tarball", "build/build/tmp")

def doEdisonBSPTest(step):
    branch = step.getProperty("otherbranch")
    if "edison" in branch:
        return True
    else:
        return False


def doEMGDTest(step):
    buildername = step.getProperty("buildername")
    branch = step.getProperty("otherbranch")
    if "edison" in branch and ("crownbay" in buildername or "fri2" in buildername):
        return True
    else:
        return False 

def getMetaParams(step):
    defaultenv['MACHINE'] = step.getProperty("machine")
    defaultenv['SDKMACHINE'] = step.getProperty("sdk")
    step.setProperty("MetaImage", step.getProperty("imagetype").replace("and", " "))
    return True

def getCleanSS(step):
    try:
        cleansstate = step.getProperty("cleansstate")
    except:
        cleansstate = False
    if cleansstate=="True" and not step.build.getProperties().has_key("donecleansstate"):
        step.setProperty("donecleansstate", True)
        return True
    else:
        return False

def setBSPLayerRepo(step):
####################
# WIP web selectable layer support
####################
    defaultenv['BSP_REPO'] = step.getProperty("layer0repo")
    defaultenv['BSP_BRANCH'] = step.getProperty("layer0branch")
    defaultenv['BSP_WORKDIR'] = "build/" + step.getProperty("layer0workdir")
    defaultenv['BSP_REV'] = step.getProperty("layer0revision")
    return True

def uploadToS3(step):
    workdir = step.getProperty("workdir")
    FILE_README = 'README'
    out = open(os.path.join(workdir, 'build/build/tmp/deploy/images/', FILE_README), "a+") 
    DEST = os.path.join(workdir, 'build/build/tmp/deploy/images/', "w+") 
#    conn = boto.connect_s3()
#    bucket = conn.get_bucket('yocto')
#    s =str(today)
#    k = Key(bucket)
#    out.write("MD5SUM for build files: \n")
#    for path, dir, files in os.walk(DEST):
#        for file in files:
#            k.key = "Releases" + "/" + s + "/" + os.path.relpath(os.path.join(path,file),DEST)
#            k.set_contents_from_filename(os.path.join(path,file))
#            out.write(k.compute_md5(open(os.path.join(path,file)))[0] + " " + str(file) + "\n")
#
#    k.key = "Releases" + "/" + s + "/" + FILE_README
#    k.set_contents_from_filename(os.path.join(DEST,FILE_README))
#
def runPostamble(factory):
    factory.addStep(ShellCommand(description=["Setting destination"],
                    command=["sh", "-c", WithProperties('echo "%s" > ./deploy-dir', "DEST")],
                    env=copy.copy(defaultenv),
                    timeout=14400))
    if PUBLISH_BUILDS == "True":
        factory.addStep(ShellCommand, warnOnFailure=True, description="Ensuring DEST directory exists",
                        command=["sh", "-c", WithProperties("mkdir -p %s", "DEST")],
                        timeout=20)
        factory.addStep(ShellCommand, description="Creating CURRENT link",
                        command=["sh", "-c", WithProperties("rm -rf %s/../CURRENT; ln -s %s %s/../CURRENT", "DEST", "DEST", "DEST")],
                        timeout=20)
        factory.addStep(ShellCommand(
                        description="Making tarball dir",
                        command=["mkdir", "-p", "yocto"],
                        env=copy.copy(defaultenv),
                        timeout=14400))
    #if defaultenv['ABTARGET'] != "oecore":
    #    factory.addStep(ShellCommand(doStepIf=getRepo, warnOnFailure=True, description="Grabbing git archive",
    #                    command=["sh", "-c", WithProperties("wget %s/snapshot/%s-%s.tar.bz2", "cgitrepo", "short-repo-name", "got_revision")],
    #                    timeout=600))
    #    factory.addStep(ShellCommand(doStepIf=getRepo, warnOnFailure=True, description="Moving tarball",  
    #                    command=["sh", "-c", WithProperties("mv %s-%s.tar.bz2 %s", "short-repo-name", "got_revision", "DEST")],
    #                    timeout=600))
    #elif defaultenv['ABTARGET'] == "oecore":
    #    factory.addStep(ShellCommand(doStepIf=setOECoreRepo, warnOnFailure=True, description="Grabbing git archive",
    #                    command=["sh", "-c", WithProperties("wget %s/snapshot/%s-%s.tar.bz2", "cgitrepo", "short-repo-name", "got_revision")],
    #                    timeout=600))
    #    factory.addStep(ShellCommand(doStepIf=setOECoreRepo, warnOnFailure=True, description="Moving tarball",
    #                    command=["sh", "-c", WithProperties("mv %s-%s.tar.bz2 %s", "short-repo-name", "got_revision", "DEST")],
    #                    timeout=600))

def buildBSPLayer(factory, distrotype, btarget, provider):
    if distrotype == "poky":
        defaultenv['DISTRO'] = 'poky'
        runImage(factory, btarget, 'core-image-sato core-image-sato-sdk core-image-minimal gumstix-console-image', distrotype, True, provider, False)
        publishArtifacts(factory, btarget, "build/build/tmp")
        publishArtifacts(factory, "ipk", "build/build/tmp")
        publishArtifacts(factory, "rpm", "build/build/tmp")
        publishArtifacts(factory, "deb", "build/build/tmp")
    elif distrotype == "poky-lsb":
        defaultenv['DISTRO'] = 'poky-lsb'
        runImage(factory, btarget, 'core-image-lsb core-image-lsb-sdk', distrotype, True, provider, False)
        publishArtifacts(factory, btarget, "build/build/tmp")
        publishArtifacts(factory, "ipk", "build/build/tmp")
        publishArtifacts(factory, "rpm", "build/build/tmp")
        publishArtifacts(factory, "deb", "build/build/tmp")
    defaultenv['DISTRO'] = 'poky'

def publishArtifacts(factory, artifact, tmpdir):
    factory.addStep(ShellCommand(description=["Setting destination"],
                    command=["sh", "-c", WithProperties('echo "%s" > ./deploy-dir', "DEST")],
                    env=copy.copy(defaultenv),
                    timeout=14400))
    factory.addStep(shell.SetProperty(workdir="build",
                        command="echo " + artifact,
                        property="ARTIFACT"))

    if PUBLISH_BUILDS == "True":
        if artifact == "adt_installer":
            factory.addStep(ShellCommand(
                            description="Making adt_installer dir",
                            command=["mkdir", "-p", WithProperties("%s/adt_installer", "DEST")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Copying adt_installer"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links *adt* %s/adt_installer", "DEST")],
                            workdir=tmpdir + "/deploy/sdk",
                            env=copy.copy(defaultenv),
                            timeout=14400))
        elif artifact == "adt_installer-QA":
            factory.addStep(ShellCommand(
                            description="Making adt_installer-QA dir",
                            command=["mkdir", "-p", WithProperties("%s/adt_installer-QA", "DEST")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Copying adt_installer for QA"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links *adt* %s/adt_installer-QA", "DEST")],
                            workdir=tmpdir + "/deploy/sdk",
                            env=copy.copy(defaultenv),
                            timeout=14400))
        elif artifact == "adtrepo-dev":
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description="removing old ipk dir",
                            command=["rm", "-rf", WithProperties("%s/%s-%s/adt-ipk", "ADTREPO_PATH", "SDKVERSION", "got_revision")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description="Making dev adtrepo ipk dir",
                            command=["mkdir", "-p", WithProperties("%s/%s-%s/adt-ipk", "ADTREPO_DEV_PATH", "SDKVERSION", "got_revision")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description=["Copying ipks for QA"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links * %s/%s-%s/adt-ipk", "ADTREPO_DEV_PATH", "SDKVERSION",  "got_revision")],
                            workdir=tmpdir + "/deploy/ipk",
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description="Making dev adtrepo images dir",
                            command=["mkdir", "-p", WithProperties("%s/%s-%s/rootfs", "ADTREPO_DEV_PATH", "SDKVERSION", "got_revision")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description=["Copying images for adtrepo-dev"],
                            command=["sh", "-c", WithProperties("for x in `ls %s/machines/qemu/|grep -v tiny`; do if [ $x != 'qemu' ]; then rsync -av %s/machines/qemu/* %s/%s-%s/rootfs; fi; done", "DEST", "DEST", "ADTREPO_DEV_PATH", "SDKVERSION", "got_revision")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description=["qemux86-64 adtrepo fix"],
                            command=["sh", "-c", WithProperties("mv %s/%s-%s/rootfs/qemux86-64 %s/%s-%s/rootfs/qemux86_64", "ADTREPO_DEV_PATH", "SDKVERSION", "got_revision", "ADTREPO_DEV_PATH", "SDKVERSION", "got_revision")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
# This could do with some DRYing up.
        elif artifact == "adtrepo":
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description="Making adtrepo ipk dir",
                            command=["mkdir", "-p", WithProperties("%s/%s-%s/adt-ipk", "ADTREPO_PATH", "SDKVERSION", "got_revision")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description=["Copying ipks for adtrepo"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links * %s/%s-%s/adt-ipk", "ADTREPO_PATH", "SDKVERSION",  "got_revision")],
                            workdir=tmpdir + "/deploy/ipk",
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description="Making adtrepo images dir",
                            command=["mkdir", "-p", WithProperties("%s/%s-%s/rootfs", "ADTREPO_PATH", "SDKVERSION", "got_revision")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description=["Copying images for adtrepo"],
                            command=["sh", "-c", WithProperties("for x in `ls %s/machines/qemu/|grep -v tiny`; do if [ $x != 'qemu' ]; then rsync -av %s/machines/qemu/* %s/%s-%s/rootfs; fi; done", "DEST", "DEST", "ADTREPO_PATH","SDKVERSION", "got_revision")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(warnOnFailure=True,
                            description=["qemux86-64 adtrepo fix"],
                            command=["mv", WithProperties("%s/%s-%s/rootfs/qemux86-64 %s/%s-%s/rootfs/qemux86_64", "ADTREPO_PATH", "SDKVERSION", "got_revision", "ADTREPO_PATH", "SDKVERSION", "got_revision")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
        elif artifact == "build-appliance":
            factory.addStep(ShellCommand(
                            description="Making build-appliance dir",
                            command=["mkdir", "-p", WithProperties("%s/build-appliance", "DEST")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Copying build-appliance"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links * %s/build-appliance", "DEST")],
                            workdir=tmpdir + "/deploy/images",
                            env=copy.copy(defaultenv),
                            timeout=14400))
        elif artifact == "toolchain":
            factory.addStep(ShellCommand(
                            description="Making toolchain deploy dir",
                            command=["mkdir", "-p", WithProperties("%s/toolchain/i686", "DEST")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Copying i686 toolchain"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links poky-eglibc-i686* %s/toolchain/i686", "DEST")],
                            workdir=tmpdir + "/deploy/sdk",
                            env=copy.copy(defaultenv), 
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Making toolchain deploy dir"],
                            command=["mkdir", '-p', WithProperties("%s/toolchain/x86_64", "DEST")],
                            env=copy.copy(defaultenv), 
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Copying x86-64 toolchain"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links poky-eglibc-x86_64* %s/toolchain/x86_64", "DEST")],
                            workdir=tmpdir + "/deploy/sdk", 
                            env=copy.copy(defaultenv),
                            timeout=14400))
        elif artifact == "oe-toolchain":
            factory.addStep(ShellCommand(
                            description="Making toolchain deploy dir",
                            command=["mkdir", "-p", WithProperties("%s/toolchain/i686", "DEST")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Copying i686 toolchain"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links oecore-i686* %s/toolchain/i686", "DEST")],
                            workdir=tmpdir + "/deploy/sdk",
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Making toolchain deploy dir"],
                            command=["mkdir", '-p', WithProperties("%s/toolchain/x86_64", "DEST")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Copying x86-64 toolchain"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links oecore-x86_64* %s/toolchain/x86_64", "DEST")],
                            workdir=tmpdir + "/deploy/sdk",
                            env=copy.copy(defaultenv),
                            timeout=14400))
        elif artifact.startswith("qemu"):
            if artifact == "qemux86-tiny":
                factory.addStep(ShellCommand(
                                description=["Making " + artifact + " deploy dir"],
                                command=["mkdir", "-p", WithProperties("%s/machines/qemu/qemux86-tiny", "DEST")],
                                env=copy.copy(defaultenv),
                                timeout=14400))
                factory.addStep(ShellCommand(
                                description=["Copying " + artifact + " artifacts"],
                                command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links * %s/machines/qemu/qemux86-tiny", 'DEST')],
                                workdir=tmpdir + "/deploy/images",
                                env=copy.copy(defaultenv),
                                timeout=14400))
            else:
                factory.addStep(ShellCommand(
                                description=["Making " + artifact + " deploy dir"],
                                command=["mkdir", "-p", WithProperties("%s/machines/qemu/%s", "DEST", "ARTIFACT")],
                                env=copy.copy(defaultenv),
                                timeout=14400))
                factory.addStep(ShellCommand(
                                description=["Copying " + artifact + " artifacts"],
                                command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links *%s* %s/machines/qemu/%s", 'ARTIFACT', 'DEST', 'ARTIFACT')],
                                workdir=tmpdir + "/deploy/images",
                                env=copy.copy(defaultenv),
                                timeout=14400))
        elif artifact.startswith("mpc8315e"):
            factory.addStep(ShellCommand(
                            description=["Making " + artifact + " deploy dir"],
                            command=["mkdir", "-p", WithProperties("%s/machines/%s", "DEST", "ARTIFACT")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Copying " + artifact + " artifacts"],
                            command=["sh", "-c", WithProperties("cp -R --no-dereference --preserve=links *mpc8315*rdb* %s/machines/%s", 'DEST', 'ARTIFACT')],
                            workdir=tmpdir + "/deploy/images",
                            env=copy.copy(defaultenv),
                            timeout=14400))
######################################################################
#
# Do not use tmp copy. They're there for debugging only. They really do make
# a mess of things.
#
######################################################################
        elif artifact == "non-lsb-tmp":
            factory.addStep(ShellCommand( 
                            description=["Making " +artifact + " deploy dir"],
                            command=["mkdir", "-p", WithProperties("%s/tmp", "DEST")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand( 
                            description=["Copying non-lsb tmp dir"],
                            command=["sh", "-c", WithProperties("cp -Rd * %s/tmp", "DEST")],
                            workdir=tmpdir, 
                            env=copy.copy(defaultenv),
                            timeout=14400))                           
                
        elif artifact == "lsb-tmp":       
            factory.addStep(ShellCommand( 
                            description=["Making " + artifact + " deploy dir"],
                            command=["mkdir", "-p", WithProperties("%s/lsb-tmp", "DEST")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand, description=["Copying non-lsb tmp dir"],
                            command=["sh", "-c", WithProperties("cp -Rd * %s/lsb-tmp", "DEST")],
                            workdir=tmpdir, 
                            env=copy.copy(defaultenv),
                            timeout=14400)                           
            
        elif artifact == "rpm" or artifact == "deb" or artifact == "ipk":        
            factory.addStep(ShellCommand, description=["Copying " + artifact],
                    command=["sh", "-c", WithProperties("rsync -av %s %s", 'ARTIFACT', 'DEST')],
                    workdir=tmpdir + "/deploy/", 
                    env=copy.copy(defaultenv),
                    timeout=14400)
            
        elif artifact == "buildstats":
            PKGDIR = os.path.join(DEST, artifact)
            factory.addStep(ShellCommand( 
                            description=["Making " + artifact + " deploy dir"],
                            command=["mkdir", "-p", WithProperties("%s/buildstats", "DEST")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand, description=["Copying " + artifact],
                            command=["sh", "-c", WithProperties("rsync -av * %s/buildstats", "DEST")],
                            workdir=tmpdir + "/buildstats", 
                            env=copy.copy(defaultenv),
                            timeout=14400)   
        else:
            factory.addStep(ShellCommand(
                            description=["Making " + artifact + " deploy dir"],
                            command=["mkdir", "-p", WithProperties("%s/machines/%s", "DEST", "ARTIFACT")],
                            env=copy.copy(defaultenv),
                            timeout=14400))
            factory.addStep(ShellCommand(
                            description=["Copying " + artifact + " artifacts"],
                            command=["sh", "-c", WithProperties("cp -Rd *%s* %s/machines/%s", 'ARTIFACT', 'DEST', 'ARTIFACT')],
                            workdir=tmpdir + "/deploy/images",
                            env=copy.copy(defaultenv),
                            timeout=14400))

    if PUBLISH_SSTATE == "True" and artifact == "sstate":
        factory.addStep(ShellCommand, description="Syncing shared state cache to mirror", 
                        command="yocto-update-shared-state-prebuilds", timeout=2400)

################################################################################
#
# Nightly Gumstix Overo Master
#
################################################################################
f97 = factory.BuildFactory()
defaultenv['DISTRO'] = 'poky'
defaultenv['ABTARGET'] = 'overo'
defaultenv['MACHINE'] = "overo"
defaultenv['BRANCH'] = "denzil"
defaultenv['ENABLE_SWABBER'] = 'false'
defaultenv['MIGPL']="False"
defaultenv['REVISION'] = "denzil"
f97.addStep(shell.SetProperty(command="echo 'master'", property="branch"))
makeCheckout(f97)
runPreamble(f97, defaultenv['ABTARGET'])
defaultenv['SDKMACHINE'] = 'i686'
runImage(f97, 'overo', defaultenv['DISTRO'], False, "gumstix", defaultenv['BUILD_HISTORY_COLLECT'])
publishArtifacts(f97, "toolchain","build/build/tmp")
publishArtifacts(f97, "ipk", "build/build/tmp")
f97.addStep(NoOp(name="nightly"))
b97 = {'name': "overo-master",
      'slavenames': ["builder1"],
      'builddir': "nightly-gumstix-master",
      'factory': f97,
      }
yocto_builders.append(b97)
#yocto_sched.append(
#		timed.Periodic(name="overo-master",
#                builderNames=["nightly-overo-master"],
#                periodicBuildTimer=7200)
#		)

################################################################################
#
# Nightly Gumstix Overo Dev 
#
################################################################################
f98 = factory.BuildFactory()
defaultenv['DISTRO'] = 'poky'
defaultenv['ABTARGET'] = 'overo'
defaultenv['MACHINE'] = "overo"
defaultenv['BRANCH'] = "danny"
defaultenv['ENABLE_SWABBER'] = 'false'
defaultenv['MIGPL']="False"
defaultenv['REVISION'] = "danny"
f98.addStep(shell.SetProperty(command="echo 'dev'", property="branch"))
makeCheckout(f98)
runPreamble(f98, defaultenv['ABTARGET'])
defaultenv['SDKMACHINE'] = 'i686'
runImage(f98, 'overo', defaultenv['DISTRO'], False, "gumstix", defaultenv['BUILD_HISTORY_COLLECT'])
publishArtifacts(f98, "toolchain","build/build/tmp")
publishArtifacts(f98, "ipk", "build/build/tmp")
f98.addStep(NoOp(name="nightly"))
b98 = {'name': "overo-dev",
      'slavenames': ["builder2"],
      'builddir': "nightly-gumstix-dev",
      'factory': f98
      }
yocto_builders.append(b98)
#yocto_sched.append(
#		timed.Periodic(name="overo-dev",
#                builderNames=["nightly-overo-dev"],
#                periodicBuildTimer=7200))

################################################################################
#
# Nightly Gumstix Duovero Master 
#
################################################################################
f99 = factory.BuildFactory()
defaultenv['DISTRO'] = 'poky'
defaultenv['ABTARGET'] = 'duovero'
defaultenv['MACHINE'] = "duovero"
defaultenv['BRANCH'] = "danny"
defaultenv['ENABLE_SWABBER'] = 'false'
defaultenv['MIGPL']="False"
defaultenv['REVISION'] = "danny"
f98.addStep(shell.SetProperty(command="echo 'master'", property="branch"))
makeCheckout(f99)
runPreamble(f99, defaultenv['ABTARGET'])
defaultenv['SDKMACHINE'] = 'i686'
runImage(f99, 'duovero', defaultenv['DISTRO'], False, "gumstix", defaultenv['BUILD_HISTORY_COLLECT'])
publishArtifacts(f99, "toolchain","build/build/tmp")
publishArtifacts(f99, "ipk", "build/build/tmp")
f99.addStep(NoOp(name="nightly"))
b99 = {'name': "duovero-master",
      'slavenames': ["builder2"],
      'builddir': "nightly-duovero-master",
      'factory': f99
      }
yocto_builders.append(b99)
#yocto_sched.append(
#		timed.Periodic(name="nightly-duovero-master",
#                builderNames=["nightly-gumstix-master"],
#                periodicBuildTimer=7200))


################################################################################
#
# Nightly Linaro 
#
################################################################################
#f95 = factory.BuildFactory()
#defaultenv['ABTARGET'] = 'nightly-linaro'
#defaultenv['ENABLE_SWABBER'] = 'false'
#runImageLinaro(f95)
#f95.addStep(NoOp(name="nightly1"))
#b95 = {'name': "nightly-linaro",
#      'slavenames': ["builder1"],
#      'builddir': "nightly-linaro",
#      'factory': f95,
#      }
#yocto_builders.append(b95)
#yocto_sched.append(
#	timed.Nightly(name='nightly-linaro-2',
#	branch=None,
#	builderNames=['nightly-linaro'],
#	hour=18,
#	minute=53))
#
#yocto_sched.append(
#		timed.Periodic(name="nightly-linaro-2",
#                builderNames=["nightly-linaro"],
#                periodicBuildTimer=600))
