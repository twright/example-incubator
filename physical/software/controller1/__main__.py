import sys

def main():
    print("physical.operation.main executing")
    print("arguments: %d" % len(sys.argv))
    if len(sys.argv) == 2:
        print("Found an argument.")
        if sys.argv[1] == "lowleveldriverserver":
            print("Starting lowleveldriverserver in a seperate process.")
        elif sys.argv[1] == "controllerphysical":
            print("Starting controllerphysical in a seperate process.")
        else:
            print("Unknown argument: " % sys.argv[1])

if __name__ == '__main__':
    main()