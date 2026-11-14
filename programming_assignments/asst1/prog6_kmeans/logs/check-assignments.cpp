#include <cassert>
#include <cstdio>
#include <vector>

#include KMEANS_SOURCE

int main(int argc, char **argv) {
  assert(argc == 2);
  FILE *output = fopen(argv[1], "wb");
  assert(output != nullptr);
  int checks = 0;
  for (int M : {0, 1, 7, 8, 9, 15, 16, 17, 127, 1001}) {
    for (int N : {1, 2, 8, 100}) {
      for (int K : {1, 3, 5}) {
        for (int range = 0; range < (K == 1 ? 2 : 3); range++) {
          std::vector<double> data(M * N), centers(K * N);
          std::vector<int> labels(M, -777);
          WorkerArgs args{0, K, data.data(), centers.data(), labels.data(),
                          nullptr, M, N, K};
          if (range == 1) args.start = K;
          if (range == 2) args.start = 1;
          for (int i = 0; i < M * N; i++) data[i] = ((i * 37 + 13) % 101 - 50) / 7.0;
          for (int i = 0; i < K * N; i++) centers[i] = ((i * 19 + 7) % 47 - 23) / 5.0;
          for (int pass = 0; pass < 2; pass++) {
            for (int i = 0; i < K * N; i++) centers[i] += ((i % 3) - 1) * 0.125;
            if (K > 1) std::copy(centers.begin(), centers.begin() + N, centers.begin() + N);
            if (M > 0) std::copy(centers.begin(), centers.begin() + N, data.begin());
            const auto oldData = data;
            const auto oldCenters = centers;
            computeAssignments(&args);
            assert(data == oldData && centers == oldCenters);
            if (M > 0 && range == 0) assert(labels[0] == 0);
            for (int k : labels) assert(k == -1 || (k >= args.start && k < args.end));
            if (M > 0) assert(fwrite(labels.data(), sizeof(int), M, output) == size_t(M));
            checks++;
          }
        }
      }
    }
  }

  for (int fixture = 0; fixture < 3; fixture++) {
    int N = fixture == 2 ? 1 : 2;
    std::vector<double> data = fixture == 0
        ? std::vector<double>{-10, -9, -9, -10, 0, 1, 1, 0, 10, 9, 9, 10}
        : fixture == 1 ? std::vector<double>{2, -3, 2, -3, 2, -3, 2, -3}
                       : std::vector<double>{-3, -2, -1, 0, 0, 0, 1, 2, 3};
    std::vector<double> centers = fixture == 0
        ? std::vector<double>{-10, -9, 0, 1, 10, 9}
        : fixture == 1 ? std::vector<double>{2, -3, 2, -3, 2, -3}
                       : std::vector<double>{-2, -2, 2};
    int M = data.size() / N;
    std::vector<int> labels(M, -777);
    const auto oldData = data;
    kMeansThread(data.data(), centers.data(), labels.data(), M, N, 3, 0.000001);
    assert(data == oldData);
    assert(fwrite(labels.data(), sizeof(int), M, output) == size_t(M));
    assert(fwrite(centers.data(), sizeof(double), centers.size(), output) == centers.size());
  }
  assert(fclose(output) == 0);
  printf("[Assignment checks]: %d\n", checks);
}
