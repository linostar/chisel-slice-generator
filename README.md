# chisel-slice-generator
A generator script for chisel slice definition files.
The script will only output one slice per package, listing all dependencies (package names not slices) and contents under that slice. The output will include a list of dependency package names and a list of file paths for contents. The output will need manual alteration to convert package names to slices, and/or to simplify the path patterns or use Chisel directives if applicable. It can serve as a good basis to create the desired slice definition files.

## How to run
Run:
```
./slice_generator.py <release_number> <arch> <package>
```

For example:
```
./slice_generator.py 24.04 amd64 libcap2
```

The output of the above example command will look like something like the following:
```yaml
package: libcap2
essentials:
  - libcap2_copyright
slices:
  all:
    essentials:
      - libc6
    contents:
      /usr/lib/x86_64-linux-gnu/libcap.so.2:
      /usr/lib/x86_64-linux-gnu/libcap.so.2.66:
      /usr/lib/x86_64-linux-gnu/libpsx.so.2:
      /usr/lib/x86_64-linux-gnu/libpsx.so.2.66:
    copyright:
      /usr/share/doc/libcap2/copyright:
```

## Implemented features
- [x] Dependency generation
- [x] Content generation
- [ ] Support for maintainer scripts
- [ ] Recognition of arch-specific dependencies
- [ ] Simplification of contents list using glob patterns
- [ ] Usage of arch-agnostic paths in contents list
- [ ] Support for chisel directives
- [x] Support for copyright slices
