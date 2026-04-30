terraform {
  backend "s3" {
    # Values are injected by deploy/destroy scripts via -backend-config flags.
  }
}
