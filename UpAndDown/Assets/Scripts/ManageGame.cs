using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class GameManager : MonoBehaviour
{

    public static string[] suits = new string[] { "C", "D", "H", "S" };
    public static string[] values = new string[] { "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K" };
    public Sprite[] cardSprites;

    int numPlayers = 0;
    public List<GameObject> playersList;

    public List<string> deck;

    // Start is called before the first frame update
    void Start()
    {

        numPlayers = 1; //TODO via network
        deck = GenerateDeck();
        Shuffle<string>(deck);
        foreach (string card in deck)
        {
            print(card);
        }

    }

    // Update is called once per frame
    void Update()
    {

    }

    public static List<string> GenerateDeck()
    {
        List<string> newDeck = new List<string>();

        foreach (string v in values)
        {
            foreach (string s in suits)
            {
                newDeck.Add(s + v);
            }
        }

        return newDeck;
    }

    void Shuffle<T>(List<T> list)
    {
        System.Random random = new System.Random();
        int n = list.Count;
        while (n > 1)
        {
            int k = random.Next(n);
            n--;
            T temp = list[k];
            list[k] = list[n];
            list[n] = temp;
        }
    }
}
