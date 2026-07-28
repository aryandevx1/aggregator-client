from loader import Loader
from pathlib import Path

def main():
    dir_path = Path(__file__).resolve()
    print(dir_path)
    curr = dir_path.parents[2] / 'aggregator-schema' / 'objects' 
    print(curr)

    loader = Loader(
        dir_path= curr
    )
    objects = loader.load()
    for obj in objects:
        print("--------------------------------------") 
        print(f"Name: {obj.name}")
        print(f"Kind: {obj.kind}")
        for field in obj.fields: 
            print(f"Name: {field.name}")
            print(f"Type: {field.type}")
            print(f"Required: {field.required}")
            print(f"Sensitive: {field.sensitive}")
            print(f"Values: {field.values}")
            print(f"Ref: {field.ref}")
            print('\n')        

if __name__ == "__main__": 
    main()