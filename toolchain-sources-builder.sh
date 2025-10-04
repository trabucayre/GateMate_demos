#!/usr/bin/bash

#
# toolchain-sources-builder.sh
#
# Copyright (C) 2025  Gwenhael Goavec-Merou <gwenhael.goavec-merou@trabucayre.com>
# SPDX-License-Identifier: MIT
#

# Install directory
: ${INSTALL_PREFIX:=/opt/gatemate}

# path where all repositories will be cloned
WORK_DIR="$(pwd)/toolchain_build"

# Option to use with cmake.
CMAKE_OPTS="-DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX"

# nextpnr options.
PEPPERCORN_PATH="$WORK_DIR/prjpeppercorn"

# Yosys Dependencies.
DEPENDENCIES="libreadline-dev zlib1g zlib1g-dev tcl-dev libffi-dev bison flex"
# prjpeppercorn Dependencies.
DEPENDENCIES="$DEPENDENCIES wget libboost-program-options-dev libboost-filesystem-dev libboost-thread-dev"

# nextpnr Dependencies.
DEPENDENCIES="$DEPENDENCIES libboost-iostreams-dev libboost-python-dev libeigen3-dev"

check_dependencies() {
	dep_install=""
	for package in $DEPENDENCIES; do
		ret=$(dpkg -l | grep $package)
		if [[ "$ret" == "" ]]; then
			#dep_install="$dep_install$package "
			dep_install+="$package "
		fi
	done

	if [[ $dep_install != "" ]]; then
		echo "Missing package: $dep_install"
		echo "sudo apt install $dep_install"
		sudo apt install $dep_install
	fi
}

git_clone_update() {
	if [[ $# == 0 ]]; then
		echo "wrong arguments"
		return
	fi

	repo=$1
	repo_dir=$WORK_DIR/$repo

	if [ -d $repo_dir ]; then
		pushd $repo_dir
		git checkout .
		git pull
		git submodule update --init --recursive
	else
		case "$repo" in
			yosys)
				repo_url="https://github.com/YosysHQ/yosys.git";;
			nextpnr)
		 		repo_url="https://github.com/YosysHQ/nextpnr";;
			prjpeppercorn)
            	repo_url="https://github.com/YosysHQ/prjpeppercorn.git";;

			*)
				echo "Error: unknown repo $repo"
				return;;
		esac

		git clone --recursive $repo_url $repo_dir
   		pushd $repo_dir
	fi

   	popd
}

clean_repo() {
	if [[ $# != 1 ]]; then
		echo "wrong arguments"
		return
	fi

	repo=$WORK_DIR/$1

	pushd $repo
	make clean
	git clean -fd .
	git clean -fX .
	git clean -fx .
	git checkout .
	git clean -fd && git clean -fX && git clean -fx
	popd
}

build_yosys() {
	repo=$WORK_DIR/$1
	pushd $repo
	make -j$(nproc)
	make install PREFIX=$INSTALL_PREFIX
	popd
}

build_prjpeppercorn() {
	repo=$WORK_DIR/$1
	pushd $repo

    mkdir -p libgm/build

    pushd libgm/build
    cmake $CMAKE_OPTS ../
    make -j$(nproc)
    make install
    popd
	popd
}

build_nextpnr() {
	# apt install libboost-iostreams-dev libboost-thread-dev libboost-program-options-dev
	# apt install libboost-python-dev libeigen3-dev
	if [[ $# > 1 ]]; then
		echo "Error: too many args"
		return
	fi

	repo=$WORK_DIR/$1

	CMD=". -B build -DUSE_OPENMP=ON -DHIMBAECHEL_UARCH=gatemate"
	CMD="$CMD -DHIMBAECHEL_PEPPERCORN_PATH=$PEPPERCORN_PATH -DHIMBAECHEL_SPLIT=ON -DARCH=himbaechel"

	pushd $repo

	cmake $CMAKE_OPTS $CMD
	cmake --build build
	cmake --install build

	popd 
}

# Check working directory. Create it when missing
[ -d $WORK_DIR ] || mkdir -p $WORK_DIR

# Check Target Directory. Create it when missing
if [ ! -d $INSTALL_PREFIX ]; then
	sudo mkdir -p $INSTALL_PREFIX
	sudo chown -R $UID:$GROUPS $INSTALL_PREFIX
fi

# check if everything must be build or only one step.
build_yosys="false"
build_prjpeppercorn="false"
build_nextpnr="false"

# No arguments or all
if [[ "$#" = 0 || $1 == "all" ]]; then
	build_yosys="true"
	build_prjpeppercorn="true"
	build_nextpnr="true"
else
	# with arguments != all
	# loop over the list
	for tgt in $@; do
		if [[ $tgt == "yosys" ]]; then
			build_yosys="true"
		fi
		if [[ $tgt == "prjpeppercorn" ]]; then
			build_prjpeppercorn="true"
		fi
		if [[ $tgt == "nextpnr" ]]; then
			build_nextpnr="true"
		fi
	done
fi

# Check/Install Dependencies
check_dependencies

# YOSYS
if [[ $build_yosys == "true" ]]; then
	git_clone_update yosys
	clean_repo yosys
	build_yosys yosys
fi

# PRJPEPPERCORN
if [[ $build_prjpeppercorn == "true" ]]; then
	git_clone_update prjpeppercorn
	clean_repo prjpeppercorn
	build_prjpeppercorn prjpeppercorn
fi

# NEXTPNR
if [[ $build_nextpnr == "true" ]]; then
	git_clone_update nextpnr
	clean_repo nextpnr
	build_nextpnr nextpnr
fi

if [ ! -d $INSTALL_PREFIX/export.sh ]; then
	echo "export PATH=$INSTALL_PREFIX/bin:\$PATH" > $INSTALL_PREFIX/export.sh
fi
