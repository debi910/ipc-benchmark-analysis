CXX := g++
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -pthread -I"include"
LDLIBS := -lrt -pthread
VENV ?= $(HOME)/.venvs/ipc-bench
STRESS_MESSAGES ?= 200000
STRESS_REPEATS ?= 3
SRC := $(wildcard src/*.cpp)
COMMON := $(filter-out src/main.cpp,$(SRC))

all: build/ipcbench

build:
	mkdir -p "build"

build/ipcbench: $(SRC) | build
	$(CXX) $(CXXFLAGS) -o "$@" $(SRC) $(LDLIBS)

build/test_stats: tests/test_stats.cpp src/stats.cpp | build
	$(CXX) $(CXXFLAGS) -o "$@" "tests/test_stats.cpp" "src/stats.cpp" $(LDLIBS)

build/test_channels: tests/test_channels.cpp $(SRC) | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -o "$@" "tests/test_channels.cpp" $(COMMON) $(LDLIBS)

build/test_shm_stress: tests/test_shm_stress.cpp $(SRC) | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -DIPC_STRESS_MESSAGES=$(STRESS_MESSAGES) -DIPC_STRESS_REPEATS=$(STRESS_REPEATS) -o "$@" "tests/test_shm_stress.cpp" $(COMMON) $(LDLIBS)

build/test_cleanup: tests/test_cleanup.cpp $(SRC) | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -o "$@" "tests/test_cleanup.cpp" $(COMMON) $(LDLIBS)

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

check: clean build/test_stats build/test_channels build/test_shm_stress build/test_cleanup
	"./build/test_stats"
	"./build/test_channels"
	"./build/test_shm_stress"
	"./build/test_cleanup"
	@! grep -RIl $$'\r' --include='Makefile' --include='*.sh' . >/dev/null

check-ci:
	$(MAKE) clean
	$(MAKE) STRESS_MESSAGES=100000 STRESS_REPEATS=2 check

bench-quick: all venv
	"$(VENV)/bin/python" "scripts/run_experiments.py" --quick

bench-full: all venv
	"$(VENV)/bin/python" "scripts/run_experiments.py" --full --resume

stress:
	$(MAKE) clean
	$(MAKE) STRESS_MESSAGES=1000000 STRESS_REPEATS=10 build/test_shm_stress
	"./build/test_shm_stress"

clean:
	rm -rf "build"
