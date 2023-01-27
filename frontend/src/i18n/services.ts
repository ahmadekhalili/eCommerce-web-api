export async function getI18NViewsVariables(
  locales: Record<string, () => Promise<unknown>>
) {
  let variables: Record<string, unknown> = {};
  for (const [key, locale] of Object.entries(locales)) {
    const dynamicRoutes = key.match(/\/views\/(.*?)\/i18n/)?.[1];
    console.log(dynamicRoutes);

    const dynamicRoutesArray = dynamicRoutes?.split("/") || [];
    let applicaitonName =
      dynamicRoutesArray[(dynamicRoutesArray?.length || 1) - 1];
    const applicationVariables: { default?: unknown } = (await locale()) || {
      default: null,
    };
    variables[applicaitonName] = applicationVariables?.default;
  }
  return variables;
}
