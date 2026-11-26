FROM gcc:14-bookworm@sha256:5e927c284bf55a7dc796262e311a0703344f62f41f5621eb56843111b1d37e15 AS build
WORKDIR /build
COPY recorder.cpp verify.py ./
RUN c++ -std=c++17 -O3 -Wall -Wextra -Werror -pedantic -static recorder.cpp -o /recorder \
    && python3 verify.py /recorder && python3 verify.py /recorder --bulk

FROM scratch
COPY --from=build /recorder /usr/local/bin/recorder
USER 65532:65532
ENTRYPOINT ["/usr/local/bin/recorder"]
