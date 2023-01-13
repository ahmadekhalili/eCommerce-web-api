const loadPlugins = (filenames: string[]) => {
    const plugins = import.meta.glob("@/plugins/*.ts");
    console.log(plugins);

    const requirePlugin = require.context('@/plugins', false, /\.js$/);
    // Create an object map to avoid nested loop for checking
    // each file passed against files found by require.context
    let fileMap = {};
    console.log(requirePlugin.keys());
    // Loop through files found and add them to the fileMap
    // Remove './' prefix so we can match filename found with plugin filenames
    // we want to import
    for (const filename of requirePlugin.keys()) {
        fileMap[filename.replace('./', '')] = true;
    }
    // Loop through plugins which we want to import
    for (const filename of filenames) {
        const filenameWithExt = `${filename}.js`;
        // Concatenate './' prefix with the file name and import the plugin
        if (Object.prototype.hasOwnProperty.call(fileMap, filenameWithExt)) {
            requirePlugin(`./${filenameWithExt}`);
        } else {
            // Throw an error if we have no match
            throw new Error(
                `No plugin found for ${filename}.
    Did you spell the plugin filename correctly?`
            );
        }
    }
};
export default loadPlugins;