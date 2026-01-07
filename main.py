try:
    from Login_Window import *
except (FileNotFoundError, ImportError, ModuleNotFoundError) as Error:
    quit("Something went horribly wrong...")

class Main(Login):
    def run(self) -> None:
        """
        Initializes the application loop starting with the Login screen.
        :return: None
        """
        self.drawLoginScreen()
        self.master.mainloop()

def main() -> None:
    """
    Entry point of the application.
    :return: None
    """
    myApp = Main()
    myApp.run()

if __name__ == "__main__":
    main()