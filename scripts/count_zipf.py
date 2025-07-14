texts = """
In the year 2134, Earth’s climate had shifted so dramatically that entire continents were redefined by ice. Antarctica had become more than just a frozen wasteland; it was a frontier — a place where the most daring scientists, outlaws, and dreamers sought refuge, discovery, or escape.

Dr. Elara Voss was neither outlaw nor dreamer. She was a physicist with a singular obsession: uncovering the truth behind a strange electromagnetic signal that had been bouncing between satellites for decades. Weak, pulsing, and utterly unnatural, the signal had become the subject of her life's work.

And now, she was closer than ever.

Her research had led her to Station Thorne, a long-abandoned research base buried under 40 feet of glacial ice. Most thought it lost to time and snow. But Elara found a way. With the help of a small expedition team—her grizzled pilot friend Roan, an AI drone named KIPP, and a contract geologist named Li—she drilled through layers of ice and history.

The hatch was frozen shut, but the old base had power. When the team forced their way in, dim emergency lights flickered to life, illuminating corridors lined with frost-covered data terminals and half-empty shelves of equipment.

“It’s like a time capsule,” Li whispered, brushing snow off a shattered display.

Elara’s eyes weren’t on the relics. They were on the terminal at the back of the main chamber, where the signal monitor sat — still glowing. Still blinking.

“It’s here,” she breathed.

KIPP hovered beside her, its lenses spinning. “Signal is identical. Frequency match: 99.998%. Estimated time of last broadcast: 54 years ago.”

Elara’s heart thudded in her chest. “Then it never stopped.”

Roan stood by the doorway, watching shadows. “And what exactly are we hoping to find, Doc? A lost radio? Some old experiment gone sideways?”

“No,” she said. “We’re hoping to find the source. The origin of the pulse.”

She accessed the terminal, fingers trembling as data began to flow — encrypted files, power logs, expedition notes. One folder was labeled simply: Project NIX.

Inside were logs dating back to 2080, with the final entry written by someone named Dr. Avery Lin.

December 3rd, 2080.

We found it. It’s alive, or… aware. Buried kilometers below the crust, under the Lake Vostok shelf. The pulse… it responds to us now. The others want to shut it down, say it’s too dangerous, too unpredictable. But we’ve already gone too far.

If you’re reading this… know that we tried.

That was the last message.

Roan stepped forward. “Too dangerous. Sounds like a warning.”

Elara’s eyes sparkled. “Or an invitation.”

They traced the coordinates logged in Dr. Lin’s final report, a deep glacial fault far beneath the base. It was too deep to drill manually, but KIPP found a tunnel — natural, perhaps seismic — leading downward.

The descent took hours. Ice turned to crystal. Rock gave way to something stranger — obsidian-like surfaces, smooth and warm despite the sub-zero environment. The tunnel ended at a vast underground chamber.

And in the center of it: the source.

It was a sphere, floating in mid-air. Not attached to anything. Emitting that same soft pulse.

KIPP’s sensors went haywire. “Material unknown. Gravity distortion: mild. Power signature: active. Warning: core temperature rising.”

Elara stepped forward, mesmerized. “It’s not human. It’s not from Earth.”

Roan swore under his breath. “You’re saying it’s alien?”

Elara nodded slowly. “Or ancient. Something we forgot. Or were never meant to find.”

She reached out and touched the sphere.

In an instant, the chamber dissolved into light.

She stood on a vast plain, stars overhead, the sky unlike anything she’d ever seen. A figure formed from starlight approached her — not walking, but existing.

“You have heard the Echo,” it said, not with words, but with intent. “We seeded it long before your kind crawled onto land.”

“Why?” Elara asked, her voice a whisper inside this impossible space.

“To see who would listen. To see who would understand that not all knowledge is safe.”

She felt a pull in her mind — memories, thoughts, everything being sifted.

“You seek truth. But truth requires cost.”

“I’ll pay it,” she said without hesitation.

The light vanished.

She collapsed onto the cavern floor, gasping.

KIPP hovered above her. “You were unconscious for 8.4 seconds. Heart rate elevated. Neural scan inconsistent with baseline.”

Roan helped her up. “What the hell happened?”

“I saw… them,” she said. “Or it. Something beyond us. It’s a message — not just a signal, but a test.”

“What kind of test?”

“To see what we do next.”

The sphere pulsed again, this time brighter.

Suddenly, cracks formed in the chamber walls. The entire cavern began to tremble.

“Earthquake?” Li shouted.

“No,” Elara said. “It’s reacting to us.”

They ran. The tunnel behind them collapsed, walls shimmering as if phasing between dimensions.

Back at the surface, the entire glacier shook. Roan got the shuttle airborne just as the ice cracked apart, revealing the tip of a monolithic structure beneath — larger than any skyscraper, buried for eons.

The sphere was only a node. A key.

Back in orbit, Elara watched the feed. All over the world, satellite data was going wild. The same pulse echoed from places no one had ever looked — deep jungles, under oceans, inside mountain ranges.

“It wasn’t the only one,” she whispered.

Roan, piloting the ship, glanced at her. “You sure you still want to chase this?”

Elara smiled faintly. “Now more than ever.”

Beneath her calm, though, was awe. And fear.

The world had changed. Not with fire or war — but with a whisper beneath the ice.
"""

# Count Zipf only top 20 most common words
def count_zipf(text, top_n=20):
    """
    Count the occurrences of each word in the text and return the top N most common words.
    
    Parameters:
    text (str): The input text to analyze.
    top_n (int): The number of top most common words to return.
    
    Returns:
    list: A list of tuples containing the top N words and their counts.
    """
    from collections import Counter
    import re
    
    # Normalize the text: lower case, remove punctuation, split into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Count occurrences of each word
    word_counts = Counter(words)
    
    # Get the top N most common words
    return word_counts.most_common(top_n)

if __name__ == "__main__":
    top_words = count_zipf(texts)
    print("Top 20 most common words:")
    for word, count in top_words:
        print(f"{word}: {count}")
    
    # Example output format
    output = [{"word": word, "count": count} for word, count in top_words]
    print("\nOutput in JSON format:")
    print(output)