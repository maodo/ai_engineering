from engine import Llm
from chain import Chainer
import logging
import sys



logger = logging.getLogger(__name__)


def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    print("Prompt chaining: outline -> gate -> blog post -> translation")
    print("Input format: topic | language   (e.g. 'why agent loops matter | French')")
    print("Interactive (type 'q' or 'exit' to quit)")
    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye !")
            return 0
        if user_input in ("q", "exit"):
            print("Bye !")
            return 0
        try:
            topic, sep, target_language = user_input.partition("|")
            topic = topic.strip()
            target_language = target_language.strip()
            if not sep or not target_language:
                target_language = input("Language: ").strip() or "French"

            agent = Llm()
            chainer = Chainer(agent)
            translation = chainer.chain(topic, target_language)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            logger.exception("Agent turn failed")
            continue  # keep the session alive on a bad turn
        print("<Blog>")
        # The generated blog post
        print(translation.text)
        print("</Blog>")


if __name__ == '__main__':
    main()
