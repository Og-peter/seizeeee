# 🎴 WAIFU & HUSBANDO CATCHER 🎴  
_A Unique & Advanced Character Collector Bot for Telegram_  

![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)  
[![Open Source](https://badges.frapsoft.com/os/v2/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)  
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com)  
[![Join Support](https://img.shields.io/badge/Join%20Support%20Chat-↗-blue)](https://t.me/Collect_em_support)  

🚀 **Available on Telegram as** [Collect Em All](https://t.me/Collect_em_AllBot)  
📞 **Need Help?** [Join Our Support Chat](https://t.me/Collect_em_support)  

---

## 🌟 What is WAIFU & HUSBANDO CATCHER?  
A next-gen **character collecting** bot that spices up your Telegram group by dropping anime characters! Compete with others to **catch, trade, and collect** the best waifus and husbandos!  

⚡ **How It Works?**  
- The bot sends random characters after every **100 messages** in the group.  
- Players **guess the character's name** using `/guess`.  
- Collect **rare, legendary, and ultra-rare** characters.  
- Trade, gift, and showcase your collection!  

🛠️ **Tech Stack:** Python 3.10 | Pyrogram | Python-Telegram-Bot v20.6  

---

## 🎮 Commands List  

### 👥 **For All Users**  
| Command | Description |
|---------|-------------|
| `/guess` | Guess the dropped character’s name |
| `/fav` | Add a character to your favorites |
| `/trade` | Trade a character with another player |
| `/gift` | Gift a character to another user |
| `/collection` | Show off your harem collection |
| `/topgroups` | View groups with the **biggest harems** |
| `/top` | View users with the **largest collections (Global)** |
| `/ctop` | View users with the **largest collection (Local Chat)** |
| `/changetime` | Adjust character spawn time **(Group Admins only)** |

### 🔧 **Sudo Commands** _(For bot maintainers)_  
| Command | Description |
|---------|-------------|
| `/upload` | Add a new character (`/upload img_url character_name anime rarity`) |
| `/delete` | Remove a character from the database |
| `/update` | Modify character stats |

### 👑 **Owner Commands**  
| Command | Description |
|---------|-------------|
| `/ping` | Check bot response time |
| `/stats` | View total **groups & users** using the bot |
| `/list` | Get a **list of all users** interacting with the bot |
| `/groups` | Get a **list of groups** where the bot is active |

---

## 🎭 Character Rarity System  

| ⭐ Rarity | Number |
|----------|--------|
| ⚪ Common | 1 |
| 🟣 Rare | 2 |
| 🟡 Legendary | 3 |
| 🟢 Ultra Rare | 4 |

🔥 **The rarer the character, the harder it is to find!**  

---

## 📦 Advanced Features  
✅ **Automatic Character Drops** *(After 100 group messages)*  
✅ **Live Trading System** *(Swap characters with friends)*  
✅ **Harem Leaderboards** *(Compete to build the biggest collection)*  
✅ **Unique Guessing Game** *(Use anime knowledge to win!)*  
✅ **Customizable Spawn Rates** *(Admins can modify drop times!)*  
✅ **Multi-Language Support** *(Coming soon!)*  

---

## 🚀 Deployment Guide  

### 🌍 Deploy on VPS (Recommended)  
```bash
sudo apt-get update && sudo apt-get upgrade -y           
sudo apt-get install python3-pip -y          
sudo pip3 install -U pip

git clone https://github.com/<YourUsername>/WAIFU-HUSBANDO-CATCHER  
cd WAIFU-HUSBANDO-CATCHER  

pip3 install -U -r requirements.txt          
sudo apt install tmux && tmux  
python3 -m shivu
