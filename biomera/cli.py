from main import Main

if __name__ == "__main__":
    process = Main("config/config.json")
    
    while True:
        try:
            cmd = input("run > ")
            result = process.execute(cmd)
            # execute() now returns (success, output, apology)
            if isinstance(result, tuple):
                success, out, apology = result
                if apology:
                    print(apology)
                print(f"$ {cmd}")
                print(out)
            else:
                print(result)
        except KeyboardInterrupt:
            break
        except Exception as e:
            process.logger.error(e)