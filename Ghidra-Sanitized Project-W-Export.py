# Import necessary Ghidra modules
from ghidra.app.script import GhidraScript
import os
import shutil

class ExportSanitizedProjectScript(GhidraScript):
    def run(self):
        print("Script started.")

        # Verify if the script is running within Ghidra's scripting environment
        print("Checking Ghidra environment...")
        if not self.isRunningHeadless():
            print("Running in Ghidra environment.")
        else:
            print("Script is running in headless mode. This script requires Ghidra GUI.")
            return

        # Attempt to get the current program using the global currentProgram
        print("Attempting to get current program using global currentProgram...")
        global currentProgram
        program = currentProgram
        if program is None:
            print("No open program found. Make sure a program is loaded before running the script. Exiting script.")
            return
        else:
            print("Current program found: " + program.getName())

        try:
            # Specify the directory to save the sanitized project
            print("Prompting user to select directory...")
            sanitized_project_dir = self.askDirectory("Select Directory to Save Sanitized Project", "Select")
            if sanitized_project_dir is None:
                print("No directory selected. Exiting script.")
                return
            print("Directory selected: " + sanitized_project_dir.getAbsolutePath())
        except Exception as e:
            print("Directory selection cancelled or failed: " + str(e))
            return

        # Sanitize the current project
        self.sanitizeProject(program)
        print("Sanitization completed.")

        # Export the sanitized project to the specified directory
        self.exportProject(program, sanitized_project_dir)
        print("Export completed to: " + sanitized_project_dir.getAbsolutePath())

    def sanitizeProject(self, program):
        print("Sanitizing project...")
        
        # Clear properties like executable path and executable format
        program.setExecutablePath("")
        program.setExecutableFormat("")

        # Clear any user-specific properties
        options = program.getOptions("Program Information")
        user_info_keys = ["Created By", "Creator Hostname", "Creator Tool", "Tool Name"]
        for key in user_info_keys:
            if options.contains(key):
                options.removeOption(key)
        print("User-specific properties cleared.")

        # Clear bookmarks if they contain user-specific information
        self.clearBookmarks(program)
        print("Bookmarks cleared.")

        # Clear analysis options and properties that may contain user-specific information
        self.clearAnalysisProperties(program)
        print("Analysis properties cleared.")

        # Clear other sensitive metadata
        self.clearOtherMetadata(program)
        print("Other metadata cleared.")

    def clearBookmarks(self, program):
        try:
            bookmarkManager = program.getBookmarkManager()
            if bookmarkManager is None:
                print("BookmarkManager is None. Exiting clearBookmarks.")
                return

            monitor = self.getMonitor()
            if monitor is None:
                print("Monitor is None. Exiting clearBookmarks.")
                return

            categories = bookmarkManager.getCategories(monitor)
            if categories is None:
                print("Categories are None. Exiting clearBookmarks.")
                return

            for category in categories:
                print("Processing category: {}".format(category))
                bookmarks = bookmarkManager.getBookmarks(category)
                for bookmark in bookmarks:
                    print("Removing bookmark: {}".format(bookmark))
                    bookmarkManager.removeBookmark(bookmark)
            print("Bookmarks sanitized.")
        except Exception as e:
            print("Error clearing bookmarks: " + str(e))
            import traceback
            traceback.print_exc()

    def clearAnalysisProperties(self, program):
        try:
            options = program.getOptions("Analysis")
            optionNames = options.getOptionNames()
            for optionName in optionNames:
                options.removeOption(optionName)
            print("Analysis properties sanitized.")
        except Exception as e:
            print("Error clearing analysis properties: " + str(e))

    def clearOtherMetadata(self, program):
        try:
            userProperties = program.getOptions("User Properties")
            propertyNames = userProperties.getOptionNames()
            for propertyName in propertyNames:
                if propertyName in ["User Name", "User Email", "User Organization"]:
                    userProperties.removeOption(propertyName)
            print("Other metadata sanitized.")
        except Exception as e:
            print("Error clearing other metadata: " + str(e))

    def exportProject(self, program, sanitized_project_dir):
        projectName = program.getDomainFile().getName()
        sanitized_project_path = os.path.join(sanitized_project_dir.getAbsolutePath(), projectName + "_sanitized")
        
        if not os.path.exists(sanitized_project_path):
            os.makedirs(sanitized_project_path)
        
        project_location = program.getDomainFile().getProjectLocator().getProjectDir().getAbsolutePath()
        
        # Copy the entire project directory to the sanitized project directory
        self.copy_tree(project_location, sanitized_project_path)
        
        # Ensure the project metadata is included
        rep_directory = os.path.join(project_location, ".rep")
        if os.path.exists(rep_directory):
            shutil.copytree(rep_directory, os.path.join(sanitized_project_path, ".rep"))
            print(".rep directory copied to sanitized project.")

        project_prp_file = os.path.join(project_location, "project.prp")
        if os.path.isfile(project_prp_file):
            shutil.copy(project_prp_file, sanitized_project_path)
            print("project.prp file copied to sanitized project.")

        # Ask the user if they want to transfer scripts to the sanitized project
        include_scripts = self.askYesNo("Include Scripts", "Do you want to include scripts in the sanitized project?")
        if include_scripts:
            # Prompt the user to select the script directory
            try:
                print("Prompting user to select the script directory...")
                script_dir = self.askDirectory("Select Script Directory", "Select")
                if script_dir is None:
                    print("No script directory selected. Skipping script transfer.")
                else:
                    script_dir_path = script_dir.getAbsolutePath()
                    print("Script directory selected: " + script_dir_path)
                    self.copyScripts(script_dir_path, sanitized_project_path)
            except Exception as e:
                print("Script directory selection cancelled or failed: " + str(e))
        else:
            print("Script transfer skipped.")

        print("Sanitized project exported to: " + sanitized_project_path)

    def copyScripts(self, script_dir_path, sanitized_project_path):
        sanitized_script_dir = os.path.join(sanitized_project_path, "scripts")
        if not os.path.exists(sanitized_script_dir):
            os.makedirs(sanitized_script_dir)
        
        for script_file in os.listdir(script_dir_path):
            full_script_path = os.path.join(script_dir_path, script_file)
            if os.path.isfile(full_script_path):
                shutil.copy(full_script_path, sanitized_script_dir)
        print("Scripts copied to sanitized project.")

    def copy_tree(self, src, dst):
        if not os.path.exists(dst):
            os.makedirs(dst)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                self.copy_tree(s, d)
            else:
                shutil.copy2(s, d)

if __name__ == "__main__":
    script = ExportSanitizedProjectScript()
    script.run()