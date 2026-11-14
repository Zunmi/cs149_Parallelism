from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


root = Path(__file__).resolve().parents[1]
logs = root / "logs"
destination = root / "data.dat"
metadata_path = logs / "data-metadata.json"
if destination.exists() or metadata_path.exists():
    raise FileExistsError("Local data or metadata already exists; keeping it unchanged")

# Reuse the starter's generation block without editing the submitted main.cpp.
source = (root / "main.cpp").read_text()
prefix, main = source.split("int main() {", 1)
setup = main.split("  // NOTE:", 1)[0]
body = main.split("  /*\n", 1)[1].split("  */", 1)[0]
assert body.count("  // writeData(") == 1
assert body.count("  //           &K, &epsilon);") == 1
body = body.replace("  // writeData(", "  writeData(", 1)
body = body.replace("  //           &K, &epsilon);", "              &K, &epsilon);", 1)
cleanup = main[main.index("  delete[] data;"):]

with tempfile.TemporaryDirectory(prefix="generate-", dir=logs) as directory:
    temporary = Path(directory)
    generated_main = temporary / "generate.cpp"
    generated_main.write_text(prefix + "int main() {" + setup + body + cleanup)
    binary = temporary / "generate"
    flags = ["-m64", "-march=native", "-O3", "-Wall", "-pthread"]
    command = ["g++", *flags, "-I" + str(root.parent / "common"),
               str(generated_main), str(root / "utils.cpp"),
               str(root / "kmeansThread.cpp"), "-o", str(binary)]
    print("Compiling the local data generator...", flush=True)
    with (logs / "data-generator-build.log").open("w") as build_log:
        subprocess.run(command, stdout=build_log, stderr=subprocess.STDOUT, check=True)
    print("Generating data using the starter's M=1000000, N=100, K=3...", flush=True)
    subprocess.run([str(binary)], cwd=temporary, check=True)

    generated = temporary / "data.dat"
    with generated.open("rb") as data_file:
        M, N, K, epsilon = struct.unpack("=iiid", data_file.read(20))
        assert (M, N, K, epsilon) == (1000000, 100, 3, 0.1)
        expected_size = 20 + 8 * M * N + 8 * K * N + 4 * M
        assert generated.stat().st_size == expected_size
        data_file.seek(0)
        checksum = hashlib.file_digest(data_file, "sha256").hexdigest()
    metadata = {
        "created": datetime.now().astimezone().isoformat(),
        "origin": "local synthetic data using the starter main.cpp generation block",
        "M": M, "N": N, "K": K, "epsilon": epsilon,
        "c_rand_seed": 7, "normal_engine_initialization": "default construction",
        "generation_centers": 10, "normal_mean": 0.0, "normal_stddev": 0.5,
        "file_bytes": expected_size, "sha256": checksum,
        "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
        "compiler_flags": flags,
        "source_sha256": {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in ["main.cpp", "utils.cpp", "kmeansThread.cpp"]
        },
    }
    os.link(generated, destination)
    with metadata_path.open("x") as output:
        json.dump(metadata, output, indent=2)
        output.write("\n")
print(f"Saved {destination} ({expected_size:,} bytes)")
print(f"SHA-256: {checksum}")
print(f"Metadata: {metadata_path}")
