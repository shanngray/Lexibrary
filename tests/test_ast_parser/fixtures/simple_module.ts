// A simple TypeScript module with basic declarations.

const MAX_RETRIES: number = 3;
let appName: string;

function greet(name: string): string {
  return "Hello " + name;
}

async function fetchData(url: string): Promise<Response> {
  return fetch(url);
}

export { greet, MAX_RETRIES };
