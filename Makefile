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
	$(CXX) $(CXXFLAGS) -DIPC_TEST -DIPC_CHANNEL_MESSAGES=$(CHANNEL_MESSAGES) -DIPC_CHANNEL_LARGE_MESSAGES=$(CHANNEL_LARGE_MESSAGES) -o "$@" "tests/test_channels.cpp" $(COMMON) $(LDLIBS)

build/test_tiny_ring: tests/test_tiny_ring.cpp $(SRC) | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -DIPCB_RING_CAPACITY=4096 -o "$@" "tests/test_tiny_ring.cpp" $(COMMON) $(LDLIBS)

build/test_shm_stress: tests/test_shm_stress.cpp $(SRC) | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -DIPC_STRESS_MESSAGES=$(STRESS_MESSAGES) -DIPC_STRESS_REPEATS=$(STRESS_REPEATS) -o "$@" "tests/test_shm_stress.cpp" $(COMMON) $(LDLIBS)

build/test_cleanup: tests/test_cleanup.cpp $(SRC) | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -o "$@" "tests/test_cleanup.cpp" $(COMMON) $(LDLIBS)

build/test_timeout: tests/test_timeout.cpp build/ipcbench | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -o "$@" "tests/test_timeout.cpp" $(LDLIBS)

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

check: CHANNEL_MESSAGES := 1000
check: CHANNEL_LARGE_MESSAGES := 100
check: clean build/ipcbench build/test_stats build/test_channels build/test_tiny_ring build/test_shm_stress build/test_cleanup build/test_timeout
	"./build/test_stats"
	"./build/test_channels"
	"./build/test_tiny_ring"
	"./build/test_shm_stress"
	"./build/test_cleanup"
	"./build/test_timeout"
	@! grep -RIl $$'\r' --include='Makefile' --include='*.sh' . >/dev/null

check-ci:
	$(MAKE) clean
	$(MAKE) STRESS_MESSAGES=100000 STRESS_REPEATS=2 CHANNEL_MESSAGES=100 CHANNEL_LARGE_MESSAGES=20 check

bench-quick: all venv
	"$(VENV)/bin/python" "scripts/run_experiments.py" --quick --output "results/quick_run.csv"

bench-full: all venv
	"$(VENV)/bin/python" "scripts/run_experiments.py" --full --output "results/raw.csv"
	"$(VENV)/bin/python" "scripts/run_experiments.py" --secondary --resume --output "results/raw.csv"

bench-secondary: all venv
	"$(VENV)/bin/python" "scripts/run_experiments.py" --secondary --resume --output "results/raw.csv"

stress:
	$(MAKE) clean
	$(MAKE) STRESS_MESSAGES=1000000 STRESS_REPEATS=10 build/test_shm_stress
	"./build/test_shm_stress"

clean:
	rm -rf "build"
