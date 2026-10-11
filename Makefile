CXX := g++
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -pthread -Iinclude
LDLIBS := -lrt -pthread
VENV ?= $(HOME)/.venvs/ipc-bench
SRC := $(wildcard src/*.cpp)
COMMON := $(filter-out src/main.cpp,$(SRC))

all: build/ipcbench

build:
	mkdir -p build

build/ipcbench: $(SRC) | build
	$(CXX) $(CXXFLAGS) -o $@ $(SRC) $(LDLIBS)

build/test_stats: tests/test_stats.cpp src/stats.cpp | build
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDLIBS)

build/test_channels: tests/test_channels.cpp $(SRC) | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -o $@ tests/test_channels.cpp $(COMMON) $(LDLIBS)

build/test_shm_stress: tests/test_shm_stress.cpp $(SRC) | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -o $@ tests/test_shm_stress.cpp $(COMMON) $(LDLIBS)

build/test_cleanup: tests/test_cleanup.cpp $(SRC) | build
	$(CXX) $(CXXFLAGS) -DIPC_TEST -o $@ tests/test_cleanup.cpp $(COMMON) $(LDLIBS)

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

check: build/test_stats build/test_channels build/test_shm_stress build/test_cleanup
	./build/test_stats
	./build/test_channels
	./build/test_shm_stress
	./build/test_cleanup
	@! grep -RIl $$'\r' --include='Makefile' --include='*.sh' . >/dev/null

check-ci: check

clean:
	rm -rf build
