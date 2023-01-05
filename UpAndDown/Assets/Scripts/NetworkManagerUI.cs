using System.Collections;
using System.Collections.Generic;
using Unity.Netcode;
using UnityEngine;
using UnityEngine.UI;

public class NetworkManagerUI : NetworkBehaviour
{

    // public GameObject parentListOfPlayers;

    [SerializeField] private Button serverBtn;
    [SerializeField] private Button clientBtn;
    [SerializeField] private Button hostBtn;
    [SerializeField] private Button leaveBtn;
    [SerializeField] private Button startBtn;
    [SerializeField] private TMPro.TMP_InputField nameInput;

    private List<string> nameLoggedPlayers;

    void DeactivateNetworkBtns()
    {
        serverBtn.interactable = false;
        clientBtn.interactable = false;
        hostBtn.interactable = false;
        nameInput.interactable = false;
        leaveBtn.interactable = true;
    }

    void ActivateNetworkBtns()
    {
        serverBtn.interactable = true;
        clientBtn.interactable = true;
        hostBtn.interactable = true;
        nameInput.interactable = true;
        leaveBtn.interactable = false;
    }

    // Start is called before the first frame update
    void Start()
    {
        startBtn.interactable = false;
        leaveBtn.interactable = false;

        serverBtn.onClick.AddListener(() =>
        {
            DeactivateNetworkBtns();
            NetworkManager.Singleton.StartServer();
        });
        clientBtn.onClick.AddListener(() =>
        {
            DeactivateNetworkBtns();
            NetworkManager.Singleton.StartClient();
            if (IsClient)
            {
                RegisterClientNameServerRpc();
            }
        });
        hostBtn.onClick.AddListener(() =>
        {
            DeactivateNetworkBtns();
            NetworkManager.Singleton.StartHost();
            if (IsClient)
            {
                RegisterClientNameServerRpc();
            }
        });
        leaveBtn.onClick.AddListener(() =>
        {
            ActivateNetworkBtns();
            NetworkManager.Singleton.Shutdown();
        });
        startBtn.onClick.AddListener(() =>
        {
            Debug.Log("Start");
        });

    }

    [ServerRpc]
    private void RegisterClientNameServerRpc()
    {
        nameLoggedPlayers.Insert((int)OwnerClientId, nameInput.text);
    }

    // Update is called once per frame
    void Update()
    {
        if (IsServer)
        {
            foreach (var id in NetworkManager.ConnectedClientsIds)
            {
                Debug.Log(id + ": " + nameLoggedPlayers[(int)id]);
                // Debug.Log(id);
            }
        }

    }
}
