#include <cstdlib>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include "quiche/balsa/balsa_frame.h"
#include "quiche/balsa/balsa_enums.h"
#include "quiche/balsa/balsa_headers.h"
#include "quiche/balsa/noop_balsa_visitor.h"

class GardenVisitor : public quiche::NoOpBalsaVisitor {};

int main() {
    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket < 0) {
        std::cerr << "socket failed\n";
        return EXIT_FAILURE;
    }

    int opt = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) <
        0) {
        std::cerr << "setsockopt failed\n";
        close(server_socket);
        return EXIT_FAILURE;
    }

    sockaddr_in server_addr{
        .sin_family = AF_INET,
        .sin_port = htons(80),
        .sin_addr = {.s_addr = INADDR_ANY},
    };

    if (bind(server_socket, (struct sockaddr *)&server_addr,
             sizeof(server_addr)) < 0) {
        std::cerr << "bind failed\n";
        close(server_socket);
        return EXIT_FAILURE;
    }

    if (listen(server_socket, SOMAXCONN) < 0) {
        std::cerr << "listen failed\n" << std::endl;
        close(server_socket);
        return 1;
    }

    while (true) {
        sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);

        int const client_socket =
            accept(server_socket, (struct sockaddr *)&client_addr, &client_len);
        if (client_socket < 0) {
            std::cerr << "accept failed\n";
            continue;
        }

        quiche::BalsaFrame frame;
        GardenVisitor visitor;
        frame.set_balsa_visitor(&visitor);
        frame.set_is_request(true);
        
        while (1) {
            while (1) {
                char socket_buffer[getpagesize()];
                ssize_t const bytes_read = read(client_socket, socket_buffer, sizeof(socket_buffer));
                if (bytes_read <= 0) {
                    break;
                }
                frame.ProcessInput(socket_buffer, bytes_read);
            }
        }
    }

    close(server_socket);
}
