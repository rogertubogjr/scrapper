# ./Dockerfile
FROM debian:bullseye

# install Chrome Stable
RUN apt-get update \
 && apt-get install -y \
      curl gnupg2 ca-certificates \
 && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
      | gpg --dearmor -o /usr/share/keyrings/google-linux-keyring.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-keyring.gpg] \
      http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update \
 && apt-get install -y google-chrome-stable \
 && rm -rf /var/lib/apt/lists/*

# run as non-root (optional but recommended)
RUN useradd -m chromeuser
USER chromeuser

# start Chrome in headless mode with remote debugging open on 0.0.0.0:9222
ENTRYPOINT ["google-chrome", \
    "--headless", \
    "--no-sandbox", \
    "--disable-gpu", \
    "--disable-dev-shm-usage", \
    "--remote-debugging-address=0.0.0.0", \
    "--remote-debugging-port=9222" ]