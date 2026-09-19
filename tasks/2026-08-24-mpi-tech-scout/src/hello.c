/* Minimal multi-node MPI proof-of-concept: process launch, point-to-point,
 * and a collective, each rank printing its own hostname to prove work
 * actually crossed VM boundaries rather than just forking locally. */
#include <mpi.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);

    int world_size, world_rank;
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

    char hostname[256];
    gethostname(hostname, sizeof(hostname));
    printf("hello from rank %d/%d on %s\n", world_rank, world_size, hostname);
    fflush(stdout);
    MPI_Barrier(MPI_COMM_WORLD);

    /* point-to-point: rank 0 -> last rank */
    if (world_size > 1) {
        int tag = 0;
        if (world_rank == 0) {
            int msg = 42;
            MPI_Send(&msg, 1, MPI_INT, world_size - 1, tag, MPI_COMM_WORLD);
            printf("[rank 0 on %s] sent %d to rank %d\n", hostname, msg, world_size - 1);
        } else if (world_rank == world_size - 1) {
            int msg = 0;
            MPI_Recv(&msg, 1, MPI_INT, 0, tag, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            printf("[rank %d on %s] received %d from rank 0\n", world_rank, hostname, msg);
        }
    }

    /* collective: sum of all ranks via MPI_Reduce */
    int local = world_rank, total = 0;
    MPI_Reduce(&local, &total, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
    if (world_rank == 0) {
        printf("[rank 0] MPI_Reduce sum of ranks 0..%d = %d\n", world_size - 1, total);
    }

    MPI_Finalize();
    return 0;
}
