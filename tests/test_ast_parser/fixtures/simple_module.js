// A simple JavaScript module with various declaration types.

function greet(name) {
  return "Hello " + name;
}

async function fetchData(url) {
  const response = await fetch(url);
  return response.json();
}

const handler = (req, res) => {
  res.send("ok");
};

const fetchUser = async (id) => {
  return await getUser(id);
};

class UserService extends BaseService {
  constructor(db) {
    super();
    this.db = db;
  }

  getUser(id) {
    return this.db.find(id);
  }

  async updateUser(id, data) {
    return await this.db.update(id, data);
  }

  static create() {
    return new UserService(null);
  }

  get name() {
    return this._name;
  }

  set name(val) {
    this._name = val;
  }
}

class EmptyClass {}

const API_URL = "https://api.example.com";
const MAX_RETRIES = 3;

export function exported_func(x, y) {
  return x + y;
}

export default class App {
  start() {
    console.log("started");
  }
}

export const EXPORTED_CONST = 42;

export { greet, handler };

module.exports = { fetchData, UserService };
