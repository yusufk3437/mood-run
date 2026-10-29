# Mood Run release notes

The browser build includes level and bonus progression, solo/multiplayer infinite runs, explicit tap-to-start, pause/visibility handling, face-based gate collision, independent gate colors, saved currency and distance records, and a looping day/night environment. Solo runs have three lives and rewarded revival.

## Multiplayer Rope Run

Both players run on one shared forward position. The host owns movement constraints and gate decisions; the guest sends steering targets and displays the host's ordered snapshots. The platform is six tiles wide, with at least 5.5 tiles of usable width including character bodies. A visible rope limits center-to-center separation to two tiles, and players pull one another when it becomes taut. Three wide gate choices span the track.

Each player has one life, with no multiplayer revival. Both players must enter the same correct gate at the same shared crossing. Either mistake ends the run on both devices, showing the same player's name under LOSER with a cheeky smiling face. Pause/resume also applies to both players; a disconnected rope run ends instead of silently becoming solo. Old-round and duplicate snapshots are ignored, and rewards are banked once. Both players must load this version to use the new protocol.

## Rewarded video adapter

Without an ad provider the game shows a clearly labelled three-second **test ad**. It does not serve paid advertising. Cancelling earns no reward.

A native wrapper or web ad provider may supply `window.MoodRunAds.showRewarded()`. Return a Promise resolving to `{ rewarded: true }` only from the provider's completed-reward callback. A close without reward, unavailable ad, load failure or rejected Promise must not return `rewarded: true`. In solo mode the game grants one life once, retains progress, and waits for another tap before resuming. Multiplayer never offers revival. Local storage balances are suitable for this prototype, not a trusted real-money economy.

## Browser regression checks

Install Python's `playwright` package and Chromium, then run `python tests/rope_run.py` from the repository. `MOOD_CHROMIUM` may point to a browser executable. These checks run two isolated browser contexts, inject test-only observers into served HTML, and connect the production message handlers through a controlled transport. They cover the rope limit, shared forward position, wider movement area, simultaneous gate choice, named failures for either player, one-life game over, pause/restart, stale messages, disconnects, and solo revival. No test hook is shipped in the game page.

## Publishing work still required

Connect a real ad SDK and production placement IDs; update the privacy notice to describe that provider. Test actual WebRTC matchmaking across Wi-Fi/mobile networks, and plan TURN relay support where direct connections fail. Test touch controls, thermal load, memory, frame pacing, accessibility and audio on real Android/iOS devices before store submission. The automated multiplayer checks use two browser pages and a controlled transport to exercise the actual game protocol; they do not certify the external PeerJS service or mobile networks.

Publisher acceptance cannot be established from visual changes alone. Real-player testing should measure tutorial completion, session length, retries, retention and rewarded-ad completion before expanding monetization. Analytics and advertising tracking are not silently enabled in this build.
