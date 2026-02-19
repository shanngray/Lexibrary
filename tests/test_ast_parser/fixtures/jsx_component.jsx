// A React JSX component file.

import React from "react";

function Button({ label, onClick }) {
  return <button onClick={onClick}>{label}</button>;
}

const Card = ({ title, children }) => {
  return (
    <div className="card">
      <h2>{title}</h2>
      <div className="card-body">{children}</div>
    </div>
  );
};

class Counter extends React.Component {
  constructor(props) {
    super(props);
    this.state = { count: 0 };
  }

  increment() {
    this.setState({ count: this.state.count + 1 });
  }

  render() {
    return (
      <div>
        <span>{this.state.count}</span>
        <button onClick={() => this.increment()}>+</button>
      </div>
    );
  }
}

export default Button;
export { Card, Counter };
