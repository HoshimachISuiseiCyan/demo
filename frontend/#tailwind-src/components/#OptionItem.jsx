import { useStore } from "../store/useStore";

export default function OptionItem({ option, answer }) {
  const { selected, showAnswer, selectOption } = useStore();

  const letter = option[0]; // "A. xxx"

  let className = "option";

  if (showAnswer) {
    if (letter === answer) className += " correct";
    else if (letter === selected) className += " wrong";
  }

  return (
    <div
      className={className}
      onClick={() => !showAnswer && selectOption(letter)}
    >
      {option}
    </div>
  );
}