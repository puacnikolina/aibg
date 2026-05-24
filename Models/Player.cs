
using Newtonsoft.Json;

namespace SharedLibrary
{
    public class Player : Entity{
        public List<Item> Inventory;
        public List<MonsterCard> Cards;
        public bool First = false;

        public Player():base()
        {
            Inventory = new List<Item>();
            Cards = new List<MonsterCard>();
        }

        public Player(List<Item> inventory, List<MonsterCard> cards, bool first)
        {
            Inventory = inventory;
            Cards = cards;
            First = first;
        }

        public Player(Player original):base(original)
        {
            Inventory = original.Inventory.Select(item => new Item(item)).ToList();
            Cards = original.Cards.Select(card => new MonsterCard(card)).ToList();
            First = original.First;
        }
    }
}