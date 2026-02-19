// A TSX component file. JSX in function bodies should be ignored.

import React from "react";

interface AppProps {
  title: string;
  count: number;
}

export function App(props: AppProps): JSX.Element {
  return (
    <div>
      <h1>{props.title}</h1>
      <span>{props.count}</span>
    </div>
  );
}

export const Greeting: React.FC<{ name: string }> = ({ name }) => {
  return <p>Hello {name}</p>;
};

export default App;
