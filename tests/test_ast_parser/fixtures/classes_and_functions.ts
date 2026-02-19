// TypeScript module with classes, interfaces, type aliases, enums, generics.

export interface IUserService {
  getUser(id: string): User;
  deleteUser(id: string): void;
}

export class UserService extends BaseService implements IUserService {
  private db: Database;

  constructor(db: Database) {
    super();
    this.db = db;
  }

  getUser(id: string): User {
    return this.db.find(id);
  }

  deleteUser(id: string): void {
    this.db.remove(id);
  }

  static create(config: Config): UserService {
    return new UserService(new Database(config));
  }

  async fetchRemote(url: string): Promise<User[]> {
    const resp = await fetch(url);
    return resp.json();
  }

  get count(): number {
    return this.db.count();
  }
}

export type UserId = string;
export type Result<T> = Success<T> | Error;

export enum Status {
  Active,
  Inactive,
  Pending,
}

export function identity<T>(value: T): T {
  return value;
}

export default class App {
  run(): void {
    console.log("running");
  }
}

const API_VERSION: number = 2;
