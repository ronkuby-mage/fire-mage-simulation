import requests
import xml.etree.ElementTree as ET
import json

_MAX_SLOTS = 27

class ItemInfo():
    
    def __init__(self, item, prev):
        self._enchant = None
        self._item = item
        self._new = False
        if item not in prev:
            self._new = True
            self._name = None
            self._armor = 0
            self._spd = 0
            self._int = 0
            self._crt = 0
            self._hit = 0
            self._slt = None
            self._set = None
            self._load_item(item)
            prev[item] = {"spd": self._spd,
                          "int": self._int,
                          "crt": self._crt,
                          "hit": self._hit,
                          "slt": self._slt,
                          "set": self._set,
                          "name": self._name,
                          "armor": self._armor}
        else:
            self._name = prev[item]["name"]
            self._armor = prev[item]["armor"]
            self._spd = prev[item]["spd"]
            self._int = prev[item]["int"]
            self._crt = prev[item]["crt"]
            self._hit = prev[item]["hit"]
            self._slt = prev[item]["slt"]
            self._set = prev[item]["set"]
            
        act_lookup = {
                23046: "sapp",
                19339: "mqg",
                18820: "toep",
                19950: "zhc"}
        if item in act_lookup:
            self._act = act_lookup[item]
        else:
            self._act = None
            
    def _load_item(self, item):
        undead = {23207: 85,
                  23085: 48,
                  23084: 35,
                  23091: 26,
                  19812: 48}
        
        r = requests.get(f"http://classic.wowhead.com/item={item:d}&xml")
        tree = ET.fromstring(r.text)

        self._name = tree.find('./item/name').text

        info = tree.find('./item/jsonEquip')
        info = json.loads("{" + info.text + "}")
        if "spldmg" in info:
            self._spd += info["spldmg"]
        if "firsplpwr" in info:
            self._spd += info["firsplpwr"]
        if item in undead:
            self._spd += undead[item]
        if "int" in info:
            self._int += info["int"]
        if "splcritstrkpct" in info:
            self._crt += info["splcritstrkpct"]
        if "splhitpct" in info:
            self._hit += info["splhitpct"]
        if "slotbak" in info:
            self._slt = info["slotbak"]
        if "itemset" in info:
            self._set = info["itemset"]
        if "armor" in info:
            self._armor = info["armor"]
            
    def add_enchant(self, item, prev, spell=False):
        self._enchant = item
        self._enchant_spell = spell
        if not spell:
            enchant = ItemInfo(item, prev)
            self._spd += enchant.spd
            self._int += enchant.intellect
            self._crt += enchant.crt
            self._hit += enchant.hit
        else:
            if item == 20025: # greater stats chest
                self._int += 4
            elif item == 13941: # stats chest
                self._int += 3
            elif item == 13822: # int bracers
                self._int += 5
            elif item == 20008: # int bracers
                self._int += 7
            elif item == 25078: # firepower gloves
                self._spd += 20
            elif item == 22749: # spellpower weapon
                self._spd += 30
        
    @property
    def spd(self):
        return self._spd

    @property
    def intellect(self):
        return self._int

    @property
    def crt(self):
        return self._crt

    @property
    def hit(self):
        return self._hit

    @property
    def itemset(self):
        return self._set

    @property
    def act(self):
        return self._act

    @property
    def slot(self):
        return self._slt
    
    @property
    def item(self):
        return self._item

    @property
    def is_new(self):
        return self._new

    @property
    def name(self):
        return self._name


class CharInfo():
    
    def __init__(self, char_file, name, saved):
        self._name = name
        with open(char_file, "rt") as fid:
            char = json.load(fid)

        self._race = char["character"]["race"].lower()
        self._atiesh = False
        self._items = []
        for item in char["items"]:
            item_info = ItemInfo(item["id"], saved)
            if item["id"] == 22589:
                self._atiesh = True
            if "enchant" in item:
                if "itemId" in item["enchant"]:
                    item_info.add_enchant(item["enchant"]["itemId"], saved)
                elif "spellId" in item["enchant"]:
                    item_info.add_enchant(item["enchant"]["spellId"], saved, spell=True)
            self._items.append(item_info)
        self._act = [item.act for item in self._items if item.act is not None]
    
    def replace(self, inc_item, saved, second=False):
        slot_map = [[idx] for idx in range(_MAX_SLOTS)]
        slot_map[5].append(20)
        slot_map[20].append(5)
        slot_map[13] += [17, 21]
        slot_map[17] += [13, 21, 23]
        slot_map[21] += [13, 17]
        slot_map[23] += [17]
        dupes = [11, 12]
 
        new_item = ItemInfo(inc_item, saved)
        
        # build up list of replacement items
        items_found = []
        for idx, item in enumerate(self._items):
            if item.slot in slot_map[new_item.slot]:
                if item.slot in dupes:
                    if not items_found or second:
                        items_found = [idx]
                else:
                    items_found.append(idx)

        # build new list
        new_items = [new_item]
        for idx, item in enumerate(self._items):
            if idx in items_found:
                if item._enchant is not None:
                    new_items[0].add_enchant(item._enchant, saved, spell=item._enchant_spell)
            else:
                new_items.append(item)
        self._items = new_items
        self._act = [item.act for item in self._items if item.act is not None]        
    
    @property
    def spd(self):
        item_spd = sum([item.spd for item in self._items])
        set_spd = 0
        # magister
        set_spd += 23*int(sum([1 for item in self._items if item.itemset == 181]) >= 4)
        # sorcerer
        set_spd += 23*int(sum([1 for item in self._items if item.itemset == 517]) >= 6)
        # arcanist
        set_spd += 18*int(sum([1 for item in self._items if item.itemset == 201]) >= 3)
        # postmaster
        set_spd += 12*int(sum([1 for item in self._items if item.itemset == 81]) >= 4)
        # rare pvp
        set_spd += 23*int(sum([1 for item in self._items if item.itemset == 542]) >= 2)
        # epic pvp
        set_spd += 23*int(sum([1 for item in self._items if item.itemset == 388]) == 6)
        # necropile
        set_spd += 23*int(sum([1 for item in self._items if item.itemset == 122]) == 5)
        # illusionist
        set_spd += 12*int(sum([1 for item in self._items if item.itemset == 482]) >= 2)
        # zanzil
        set_spd += 6*int(sum([1 for item in self._items if item.itemset == 462]) == 2)

        return item_spd + set_spd

    @property
    def crt(self):
        item_crt = sum([item.crt for item in self._items])
        set_crt = 0
        # bloodvine
        set_crt += 2*int(sum([1 for item in self._items if item.itemset == 421]) == 3)

        return item_crt + set_crt

    @property
    def hit(self):
        item_hit = sum([item.hit for item in self._items])
        set_hit = 0
        
        #zanzil
        set_hit += int(sum([1 for item in self._items if item.itemset == 462]) == 2)

        return item_hit + set_hit

    @property
    def intellect(self):
        race_int = {
                "human": 125,
                "gnome": 139,
                "undead": 123,
                "troll": 121}
        if self._race in race_int:
            base_int = race_int[self._race]
        else:
            base_int = 0
        item_int = sum([item.intellect for item in self._items])

        return base_int + item_int

    @property
    def race(self):
        return self._race

    @property
    def is_udc(self):
        return sum([1 for item in self._items if item.itemset == 536]) == 3

    @property
    def act(self):
        return self._act

    @property
    def atiesh(self):
        return self._atiesh

    @property
    def name(self):
        return self._name

    @property
    def is_new(self):
        return any([item.is_new for item in self._items])
