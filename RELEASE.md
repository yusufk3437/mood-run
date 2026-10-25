# Mood Run release notes

The browser build includes level and bonus progression, solo/multiplayer infinite runs, three lives per player, explicit tap-to-start, per-player revival, pause/visibility handling, face-based gate collision, independent gate colors, saved currency and infinite distance records, and a looping day/night environment.

## Rewarded video adapter

Without an ad provider the game shows a clearly labelled three-second **test ad**. It does not serve paid advertising. Cancelling earns no reward.

A native wrapper or web ad provider may supply `window.MoodRunAds.showRewarded()`. Return a Promise resolving to `{ rewarded: true }` only from the provider's completed-reward callback. A close without reward, unavailable ad, load failure or rejected Promise must not return `rewarded: true`. The game grants one life once, retains run progress, and waits for another tap before resuming. Each player can revive independently. Local storage balances are suitable for this prototype, not a trusted real-money economy.

## Publishing work still required

Connect a real ad SDK and production placement IDs; update the privacy notice to describe that provider. Test actual WebRTC matchmaking across Wi-Fi/mobile networks, and plan TURN relay support where direct connections fail. Test touch controls, thermal load, memory, frame pacing, accessibility and audio on real Android/iOS devices before store submission. The automated multiplayer checks use two browser pages and a controlled transport to exercise the actual game protocol; they do not certify the external PeerJS service or mobile networks.

Publisher acceptance cannot be established from visual changes alone. Real-player testing should measure tutorial completion, session length, retries, retention and rewarded-ad completion before expanding monetization. Analytics and advertising tracking are not silently enabled in this build.
